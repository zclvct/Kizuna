# Live2D Widget - 使用 WebEngineView + pixi-live2d-display
import sys
from pathlib import Path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

import json
from PySide6.QtWidgets import QFrame, QVBoxLayout, QWidget
from PySide6.QtCore import Qt, Signal, QTimer, QPoint, QUrl
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineSettings
from PySide6.QtGui import QCursor
from utils import get_config, get_character_manager, get_logger
from utils.constants import resolve_path, BUILTIN_ASSETS_DIR

logger = get_logger()

# HTML 页面路径（优先使用打包环境可用的内置资源目录）
LIVE2D_HTML_DIR = BUILTIN_ASSETS_DIR / "live2d_web"
LIVE2D_HTML_PATH = LIVE2D_HTML_DIR / "index.html"


class _MouseOverlay(QWidget):
    """透明覆盖层 - 拦截 QWebEngineView 上的所有鼠标事件"""

    clicked = Signal()
    drag_started = Signal(QPoint)
    tapped = Signal(float, float)  # (x, y) 相对坐标

    def __init__(self, parent=None):
        super().__init__(parent)
        # 透明且可接收鼠标事件
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.setMouseTracking(True)

        self._press_pos = None
        self._is_dragging = False
        self._drag_threshold = 5

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._press_pos = event.position().toPoint()
            self._is_dragging = False
            event.accept()
        else:
            # 右键/中键: ignore 让 Qt 事件冒泡到父链
            # 最终由 MainWindow.contextMenuEvent 处理
            event.ignore()

    def mouseMoveEvent(self, event):
        if self._press_pos is not None and not self._is_dragging:
            current_pos = event.position().toPoint()
            distance = (current_pos - self._press_pos).manhattanLength()
            if distance > self._drag_threshold:
                self._is_dragging = True
                global_pos = self.mapToGlobal(self._press_pos)
                self.drag_started.emit(global_pos)
                logger.debug("Overlay: 开始拖拽")
            event.accept()
        else:
            # 非拖拽时 ignore，让事件传播给父控件
            event.ignore()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if not self._is_dragging and self._press_pos is not None:
                self.clicked.emit()
                x = event.position().x()
                y = event.position().y()
                self.tapped.emit(x, y)
            self._press_pos = None
            self._is_dragging = False
        event.accept()

    # 不重写 contextMenuEvent，让事件自然冒泡到 MainWindow


class Live2DGLWidget(QFrame):
    """Live2D WebEngine 渲染控件 - QFrame 包裹 QWebEngineView + 透明 Overlay"""
    clicked = Signal()
    drag_started = Signal(QPoint)
    size_changed = Signal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.model = None  # 保留兼容性
        self._scale = get_config().general.model_scale
        self._initialized = False
        self._model_loaded = False
        self._pending_model_path = None
        self._motion_map = {}
        self._expression_names = []
        self._model_config = None

        # 模型自然尺寸（将在模型加载后从 JS 查询）
        self._model_natural_width = 0
        self._model_natural_height = 0

        # 眼球追踪
        self._eye_target_x = 0.0
        self._eye_target_y = 0.0
        self._eye_current_x = 0.0
        self._eye_current_y = 0.0
        self._eye_smoothing = 0.15

        logger.info("创建 Live2D WebEngine 控件")

        # 透明背景
        self.setStyleSheet("background: transparent; border: none;")

        # 内部布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # QWebEngineView 渲染层
        self._web_view = QWebEngineView()
        self._web_view.setStyleSheet("background: transparent; border: none;")
        self._web_view.page().setBackgroundColor(Qt.GlobalColor.transparent)
        layout.addWidget(self._web_view, 1)

        # 透明鼠标覆盖层（直接子控件，覆盖整个区域）
        self._overlay = _MouseOverlay(self)

        # 允许本地页面访问本地文件（Windows 下更严格，显式开启）
        settings = self._web_view.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.Accelerated2dCanvasEnabled, True)

        # 加载本地 HTML
        if LIVE2D_HTML_PATH.exists():
            url = QUrl.fromLocalFile(str(LIVE2D_HTML_PATH.absolute()))
            # 先连接信号再 load，避免页面秒开导致错过 loadFinished
            self._web_view.loadFinished.connect(self._on_page_loaded)
            self._web_view.load(url)
        else:
            logger.error(f"Live2D HTML 文件不存在: {LIVE2D_HTML_PATH}")

        # Overlay 信号连接
        self._overlay.clicked.connect(self.clicked.emit)
        self._overlay.drag_started.connect(self.drag_started.emit)
        self._overlay.tapped.connect(self._on_tap)

        # 眼球追踪定时器 (15 FPS 足够流畅，避免 JS 调用积压)
        self._eye_timer = QTimer()
        self._eye_timer.timeout.connect(self._update_eye_tracking)
        self._eye_timer.start(66)  # ~15 FPS

        # 延迟初始化 canvas 尺寸（等待 widget 被布局）
        QTimer.singleShot(50, self._init_canvas_size)

    def resizeEvent(self, event):
        """窗口大小改变 - 同步 overlay 大小并通知 JS"""
        super().resizeEvent(event)
        # Overlay 覆盖整个控件
        self._overlay.setGeometry(0, 0, self.width(), self.height())
        w, h = self.width(), self.height()
        if w > 0 and h > 0:
            self._run_js(f"resizeView({w}, {h})")

    def _on_tap(self, x: float, y: float):
        """Overlay 点击 → 触发模型触摸"""
        self._run_js(f"tapModel({x}, {y})")

    def _init_canvas_size(self):
        """延迟初始化 canvas 尺寸"""
        w, h = self.width(), self.height()
        if w > 0 and h > 0 and self._initialized:
            logger.info(f"延迟初始化 canvas 尺寸: {w}x{h}")
            self._run_js(f"resizeView({w}, {h})")

    def _on_page_loaded(self, ok):
        """页面加载完成"""
        if ok:
            self._initialized = True
            logger.info("Live2D WebEngine 页面加载成功")

            # 测试 JS 环境是否正常工作
            self._run_js("console.log('JS environment test passed')")

            # 立即初始化 canvas 尺寸（使用当前 widget 尺寸）
            w, h = self.width(), self.height()
            if w > 0 and h > 0:
                logger.info(f"初始化 canvas 尺寸: {w}x{h}")
                self._run_js(f"resizeView({w}, {h})")

            # 延迟加载模型，确保 canvas 尺寸已设置
            if self._pending_model_path:
                # 使用默认参数捕获当前值，避免闭包问题
                path = self._pending_model_path
                self._pending_model_path = None
                QTimer.singleShot(100, lambda p=path: self._load_model_internal(p))
        else:
            logger.error("Live2D WebEngine 页面加载失败")

    def _run_js(self, js_code, callback=None):
        """执行 JavaScript 代码"""
        if not self._initialized:
            return
        try:
            if callback:
                self._web_view.page().runJavaScript(js_code, callback)
            else:
                self._web_view.page().runJavaScript(js_code)
        except Exception as e:
            logger.error(f"执行 JS 失败: {e}")

    def _check_live2d_web_assets(self) -> bool:
        """检查 Web 端 Live2D 依赖文件是否存在"""
        required_files = [
            LIVE2D_HTML_PATH,
            LIVE2D_HTML_DIR / "libs" / "pixi.min.js",
            LIVE2D_HTML_DIR / "libs" / "live2dcubismcore.min.js",
            LIVE2D_HTML_DIR / "libs" / "cubism4.min.js",
        ]
        missing = [str(p) for p in required_files if not p.exists()]
        if missing:
            logger.error("Live2D Web 资源缺失: " + ", ".join(missing))
            return False
        return True

    def load_model(self, model_path: str):
        """加载 Live2D 模型"""
        if not self._initialized:
            logger.info(f"页面尚未加载，延迟加载模型: {model_path}")
            self._pending_model_path = model_path
            return True
        return self._load_model_internal(model_path)

    def _load_model_internal(self, model_path: str):
        """内部加载模型方法"""
        try:
            logger.info(f"开始加载模型: {model_path}")
            self._model_loaded = False

            if not self._check_live2d_web_assets():
                raise FileNotFoundError("Live2D Web 资源缺失，请检查打包文件")

            if not model_path:
                raise ValueError("model_path 为空，请检查配置文件中的 live2d.model_path 设置")

            model_path_obj = resolve_path(model_path)
            logger.info(f"模型路径解析: {model_path_obj}, 存在: {model_path_obj.exists()}")

            if not model_path_obj.exists():
                fallback_model_path = BUILTIN_ASSETS_DIR / "live2d" / "biaoqiang"
                logger.info(f"尝试回退模型路径: {fallback_model_path}, 存在: {fallback_model_path.exists()}")
                if fallback_model_path.exists():
                    logger.warning(
                        f"模型目录不存在，自动回退到内置模型: {fallback_model_path} "
                        f"(原始: {model_path}, 解析后: {model_path_obj})"
                    )
                    model_path_obj = fallback_model_path
                else:
                    raise FileNotFoundError(f"模型目录不存在: {model_path} (解析后: {model_path_obj})")

            model3_files = list(model_path_obj.glob("*.model3.json"))
            logger.info(f"在 {model_path_obj} 找到 {len(model3_files)} 个 .model3.json 文件")

            if not model3_files:
                raise FileNotFoundError(f"未找到 .model3.json 文件在: {model_path_obj}")

            model_json_path = model3_files[0]
            logger.info(f"找到模型文件: {model_json_path}, 绝对路径: {model_json_path.absolute()}")

            # 检查文件是否可读
            try:
                with open(model_json_path, 'r', encoding='utf-8') as f:
                    test_content = f.read(100)
                    logger.info(f"模型文件可读，前100字符: {test_content[:50]}...")
            except Exception as file_err:
                raise FileNotFoundError(f"无法读取模型文件 {model_json_path}: {file_err}")

            # 解析动作映射（Python 端保持缓存）
            self._parse_model_motions(model_json_path)

            # 使用 file:// URL 加载模型
            model_url = QUrl.fromLocalFile(str(model_json_path.absolute())).toString()
            logger.info(f"模型 URL: {model_url}")

            # 验证 URL 格式（Windows 下可能是 file:///C:/ 或 file://C:/）
            if not model_url.startswith("file:///") and not model_url.startswith("file://"):
                logger.error(f"模型 URL 格式异常: {model_url}")
                # 手动构造正确的 file:// URL
                import urllib.parse
                abs_path = str(model_json_path.absolute())
                # 将反斜杠转换为正斜杠
                abs_path = abs_path.replace('\\', '/')
                if not abs_path.startswith('/'):
                    # Windows 盘符路径，添加 /
                    abs_path = '/' + abs_path
                model_url = 'file://' + abs_path
                logger.info(f"手动修正后的模型 URL: {model_url}")

            safe_model_url = json.dumps(model_url)
            logger.info(f"准备执行的 JS 代码: initLive2D({safe_model_url})...")

            js_code = (
                f"initLive2D({safe_model_url})"
                ".then((r) => JSON.stringify(r))"
                ".catch((e) => JSON.stringify({ok:false,error:(e && e.message) ? e.message : String(e)}))"
                ".catch((e) => JSON.stringify({ok:false,error:'Unknown error'}))"
            )

            logger.info("发送 JS 请求到 WebEngine...")
            self._run_js(js_code, self._on_model_init_result)

            return True

        except Exception as e:
            logger.error(f"加载模型失败: {e}", exc_info=True)
            return False

    def _on_model_init_result(self, result):
        """模型初始化结果回调"""
        try:
            # 处理空字符串或 None 的情况（Windows 打包环境可能出现）
            if not result or not isinstance(result, str) or not result.strip():
                self._model_loaded = False
                logger.error(f"处理模型初始化结果失败: 收到空响应，原始返回: {repr(result)}")
                return

            payload = json.loads(result)

            if isinstance(payload, dict):
                ok = bool(payload.get("ok", False))
                if ok:
                    self._model_loaded = True
                    logger.info("WebEngine Live2D 模型加载完成")
                    QTimer.singleShot(500, self._query_model_dimensions)
                else:
                    self._model_loaded = False
                    error = payload.get("error", "未知错误")
                    logger.error(f"WebEngine Live2D 模型加载失败: {error}")
            elif payload is True:
                self._model_loaded = True
                logger.info("WebEngine Live2D 模型加载完成")
                QTimer.singleShot(500, self._query_model_dimensions)
            else:
                self._model_loaded = False
                logger.error(f"WebEngine Live2D 模型加载失败，返回值: {payload}")
        except json.JSONDecodeError as e:
            self._model_loaded = False
            logger.error(f"处理模型初始化结果失败（JSON解析错误）: {e}, 原始返回: {repr(result)}")
        except Exception as e:
            self._model_loaded = False
            logger.error(f"处理模型初始化结果失败: {e}, 原始返回: {repr(result)}")

    def _query_model_dimensions(self):
        """从 JS 查询模型实际像素尺寸"""
        self._run_js("getModelInfo()", self._on_model_dimensions_received)

    def _on_model_dimensions_received(self, result):
        """处理从 JS 查询到的模型尺寸"""
        if result:
            try:
                info = json.loads(result)
                self._model_natural_width = info.get('width', 0)
                self._model_natural_height = info.get('height', 0)
                logger.info(f"模型实际尺寸: {self._model_natural_width}x{self._model_natural_height}")
            except Exception as e:
                logger.warning(f"解析模型尺寸失败: {e}")
        self._emit_recommended_size()

    def _parse_model_motions(self, model_json_path: Path):
        """从模型配置文件解析动作映射"""
        try:
            with open(model_json_path, 'r', encoding='utf-8') as f:
                self._model_config = json.load(f)

            file_refs = self._model_config.get("FileReferences", {})
            motions = file_refs.get("Motions", {})
            self._motion_map = {}
            self._expression_names = []

            for group_name, motion_list in motions.items():
                for index, motion_entry in enumerate(motion_list):
                    file_path = motion_entry.get("File", "")
                    if file_path:
                        motion_name = Path(file_path).stem
                        if motion_name.endswith(".motion3"):
                            motion_name = motion_name[:-8]
                        self._motion_map[motion_name] = index
                        logger.debug(f"解析动作: {motion_name} -> 索引 {index} (组: '{group_name}')")

            expressions = file_refs.get("Expressions", [])
            for exp in expressions:
                if not isinstance(exp, dict):
                    continue
                exp_name = exp.get("Name") or Path(exp.get("File", "")).stem
                if exp_name and exp_name not in self._expression_names:
                    self._expression_names.append(exp_name)

            logger.info(f"从模型解析到 {len(self._motion_map)} 个动作: {list(self._motion_map.keys())}")
            logger.info(f"从模型解析到 {len(self._expression_names)} 个表情/换装: {self._expression_names}")

        except Exception as e:
            logger.error(f"解析模型动作失败: {e}", exc_info=True)
            self._motion_map = {"idle": 0}
            self._expression_names = []

    def _emit_recommended_size(self):
        """发出推荐的窗口大小"""
        scale = max(0.5, min(2.0, float(self._scale)))

        if self._model_natural_width > 0 and self._model_natural_height > 0:
            # 基于模型实际像素尺寸和宽高比计算窗口大小
            # 目标宽度约 350px（可被 model_scale 调节）
            target_width = int(350 * scale)
            aspect = self._model_natural_height / self._model_natural_width
            target_height = int(target_width * aspect)
        else:
            # 无尺寸信息时使用默认值
            target_width = int(350 * scale)
            target_height = int(500 * scale)

        # 边距保护
        recommended_width = max(200, min(600, target_width))
        recommended_height = max(300, min(900, target_height))

        logger.info(f"推荐窗口大小: {recommended_width}x{recommended_height} (scale: {scale})")
        self.size_changed.emit(recommended_width, recommended_height)

    def get_available_motions(self) -> list:
        """获取模型支持的所有动作名称列表"""
        return list(self._motion_map.keys())

    def get_available_expressions(self) -> list:
        """获取模型支持的表情/换装名称列表"""
        return list(self._expression_names)

    def set_scale(self, scale: float):
        """设置缩放 - 通过改变窗口大小实现"""
        self._scale = max(0.5, min(2.0, float(scale)))
        # 不再调用 JS 的 setScale，而是通过改变窗口大小实现
        if self._model_loaded:
            self._emit_recommended_size()

    def play_motion(self, motion_name: str):
        """播放动作"""
        if not self._initialized:
            return

        try:
            logger.info(f"播放动作: {motion_name}")

            if not self._motion_map:
                logger.warning("动作映射表为空，无法播放动作")
                return

            motion_no = self._motion_map.get(motion_name)
            if motion_no is None:
                available = list(self._motion_map.keys())
                logger.warning(f"动作 '{motion_name}' 不在映射表中，可用动作: {available}")
                motion_no = self._motion_map.get("idle", 0)

            self._run_js(f"playMotion('{motion_name}', '', 3)")
        except Exception as e:
            logger.error(f"播放动作失败: {e}", exc_info=True)

    def update_mood(self, mood: str):
        """更新心情"""
        if not self._initialized:
            return
        try:
            logger.info(f"更新心情: {mood}")
            self._run_js(f"setMood('{mood}')")
        except Exception as e:
            logger.error(f"更新心情失败: {e}", exc_info=True)

    def play_expression(self, expression_name: str):
        """播放表情/换装"""
        if not self._initialized or not expression_name:
            return
        try:
            safe_name = expression_name.replace("'", "\\'")
            logger.info(f"播放表情/换装: {expression_name}")
            self._run_js(f"playExpression('{safe_name}')")
        except Exception as e:
            logger.error(f"播放表情/换装失败: {e}", exc_info=True)

    def _update_eye_tracking(self):
        """更新眼球追踪"""
        if not self._model_loaded:
            return

        try:
            global_pos = self.mapToGlobal(self.rect().center())
            mouse_pos = QCursor.pos()

            max_distance = 300
            dx = (mouse_pos.x() - global_pos.x()) / max_distance
            dy = -(mouse_pos.y() - global_pos.y()) / max_distance

            self._eye_target_x = max(-1.0, min(1.0, dx))
            self._eye_target_y = max(-1.0, min(1.0, dy))

            self._eye_current_x += (self._eye_target_x - self._eye_current_x) * self._eye_smoothing
            self._eye_current_y += (self._eye_target_y - self._eye_current_y) * self._eye_smoothing

            self._run_js(f"setEyeTracking({self._eye_current_x:.4f}, {self._eye_current_y:.4f})")
        except Exception as e:
            logger.debug(f"眼球追踪更新失败: {e}")


class Live2DWidget(QFrame):
    """Live2D 桌面宠物控件"""

    clicked = Signal()
    motion_played = Signal(str)
    drag_started = Signal(QPoint)
    size_changed = Signal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.character_manager = get_character_manager()
        self._current_motion = "idle"
        self._setup_ui()
        self._setup_idle_timer()
        self._load_model()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Live2D WebEngine 控件
        self.live2d_widget = Live2DGLWidget()
        self.live2d_widget.setMinimumSize(140, 215)
        self.live2d_widget.clicked.connect(self._on_live2d_clicked)
        self.live2d_widget.drag_started.connect(self.drag_started)
        self.live2d_widget.size_changed.connect(self._on_size_changed)
        layout.addWidget(self.live2d_widget, 1)
        logger.info("使用 Live2D WebEngine 渲染")

        # 透明背景
        self.setStyleSheet("""
            QFrame {
                background-color: transparent;
            }
        """)

        # 设置初始大小：优先使用上次保存的主窗口大小，避免启动后再跳变
        cfg = get_config().general
        initial_w = max(140, int(cfg.window_width) - 20) if int(cfg.window_width) > 0 else 350
        initial_h = max(215, int(cfg.window_height) - 20) if int(cfg.window_height) > 0 else 500
        self.setFixedSize(initial_w, initial_h)
        logger.info(f"Live2DWidget 初始大小: {initial_w}x{initial_h}")

    def _load_model(self):
        """加载模型"""
        try:
            config = get_config()
            model_path = config.live2d.model_path
            logger.info(f"Live2D 模型路径: {model_path}")
            # 延迟 300ms 加载模型，确保窗口布局完成
            QTimer.singleShot(300, self._do_load_model)
        except Exception as e:
            logger.error(f"加载模型时出错: {e}", exc_info=True)

    def _do_load_model(self):
        """实际执行模型加载"""
        try:
            config = get_config()
            model_path = config.live2d.model_path
            if not model_path:
                logger.error("model_path 为空，请检查配置文件中的 live2d.model_path 设置")
                return
            
            # 确保 canvas 尺寸已正确设置
            w, h = self.live2d_widget.width(), self.live2d_widget.height()
            logger.info(f"加载模型前 canvas 尺寸: {w}x{h}")
            if w > 0 and h > 0:
                self.live2d_widget._run_js(f"resizeView({w}, {h})")
            
            ok = self.live2d_widget.load_model(model_path)
            if not ok:
                logger.error(f"Live2D 模型加载启动失败: {model_path}")
        except Exception as e:
            logger.error(f"加载模型时出错: {e}", exc_info=True)

    def _setup_idle_timer(self):
        """设置空闲动画计时器"""
        self._idle_timer = QTimer()
        self._idle_timer.timeout.connect(self._on_idle)

        from live2d_renderer.motion_controller import MotionController
        motion_controller = MotionController()
        settings = motion_controller.config.get("settings", {})
        enable_idle = settings.get("enable_idle_motion", True)
        interval = settings.get("idle_interval_seconds", 30) * 1000

        if enable_idle:
            self._idle_timer.start(interval)
            logger.info(f"空闲动作已启用，间隔 {interval/1000} 秒")

    def _on_idle(self):
        """空闲动作"""
        self.play_motion("idle")

    def _on_live2d_clicked(self):
        """Live2D 控件点击"""
        self.clicked.emit()
        self._on_click()

    def _on_click(self):
        """点击互动"""
        import random
        interactive_motions = ["touch_head", "touch_body", "main_1"]
        motion = random.choice(interactive_motions)
        self.play_motion(motion)

    def _on_size_changed(self, width: int, height: int):
        """处理窗口大小变化"""
        self.setFixedSize(width, height)
        self.size_changed.emit(width, height)
        logger.info(f"Live2DWidget 大小调整为: {width}x{height}")

    def play_motion(self, motion_id: str, mood: str = None):
        """播放动作"""
        from live2d_renderer.motion_controller import MotionController
        motion_controller = MotionController()
        settings = motion_controller.config.get("settings", {})
        enable_chat_motion = settings.get("enable_chat_motion", True)

        if motion_id is None:
            logger.warning("motion_id is None, skipping motion playback")
            return

        if motion_id.startswith("idle") and not enable_chat_motion:
            return

        self._current_motion = motion_id
        self.live2d_widget.play_motion(motion_id)

        if mood:
            self.live2d_widget.update_mood(mood)

        self.motion_played.emit(motion_id)

    def update_mood(self, mood: str):
        """更新心情"""
        self.live2d_widget.update_mood(mood)

        from live2d_renderer.motion_controller import MotionController
        motion_controller = MotionController()
        motion = motion_controller.get_motion_for_mood(mood)
        if motion:
            self.play_motion(motion)

    def set_scale(self, scale: float):
        """设置模型缩放"""
        self.live2d_widget.set_scale(scale)

    def get_available_expressions(self) -> list:
        """获取模型支持的表情/换装列表"""
        return self.live2d_widget.get_available_expressions()

    def play_expression(self, expression_name: str):
        """播放表情/换装"""
        self.live2d_widget.play_expression(expression_name)
