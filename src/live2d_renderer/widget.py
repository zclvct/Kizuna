# Live2D Widget - 使用 live2d-py
import sys
from pathlib import Path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from PySide6.QtWidgets import QFrame, QVBoxLayout
from PySide6.QtCore import Qt, Signal, QTimer, QPoint
from PySide6.QtGui import QSurfaceFormat
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from OpenGL import GL
from utils import get_config, get_character_manager, get_logger

logger = get_logger()

# 导入 live2d-py (按官方文档方式)
import live2d.v3 as live2d


class Live2DGLWidget(QOpenGLWidget):
    """Live2D OpenGL 渲染控件"""
    clicked = Signal()
    drag_started = Signal(QPoint)  # 开始拖拽信号，传递全局坐标
    size_changed = Signal(int, int)  # 窗口大小变化信号 (width, height)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.model = None
        self._scale = 1.0
        self._initialized = False
        self._model_loaded = False
        self._pending_model_path = None
        self._motion_map = {}  # 动态动作映射: {motion_name: index}
        self._model_config = None  # 模型配置数据
        
        # 模型的自然尺寸（在 scale=1.0 时的显示大小）
        self._model_natural_width = 300
        self._model_natural_height = 430
        
        # 拖拽相关
        self._press_pos = None  # 按下时的位置
        self._is_dragging = False
        self._drag_threshold = 5  # 拖拽阈值（像素）
        
        # 眼睛追踪
        self._eye_target_x = 0.0  # 目标眼球X位置 (-1 到 1)
        self._eye_target_y = 0.0  # 目标眼球Y位置 (-1 到 1)
        self._eye_current_x = 0.0  # 当前眼球X位置
        self._eye_current_y = 0.0  # 当前眼球Y位置
        self._eye_smoothing = 0.15  # 眼球移动平滑度
        
        logger.info("创建 Live2D OpenGL 控件")

        # 设置 OpenGL 格式
        fmt = QSurfaceFormat()
        fmt.setAlphaBufferSize(8)
        fmt.setDepthBufferSize(24)
        fmt.setStencilBufferSize(8)
        fmt.setSamples(4)
        QSurfaceFormat.setDefaultFormat(fmt)

        # 动画定时器 (~60 FPS)
        self._animation_timer = QTimer()
        self._animation_timer.timeout.connect(self._on_animation_tick)
        self._animation_timer.start(16)
        
        # 设置鼠标追踪
        self.setMouseTracking(True)

    def initializeGL(self):
        """初始化 OpenGL"""
        logger.info("初始化 OpenGL...")
        try:
            live2d.init()
            live2d.glInit()

            # 禁用 Live2D SDK 的 INFO 日志，只显示 WARNING 和 ERROR
            live2d.setLogLevel(live2d.Live2DLogLevels.LV_WARN)

            self._initialized = True
            logger.info("OpenGL 和 Live2D 初始化成功")

            if self._pending_model_path:
                logger.info(f"OpenGL 初始化完成，加载模型: {self._pending_model_path}")
                self._load_model_internal(self._pending_model_path)
                self._pending_model_path = None

        except Exception as e:
            logger.error(f"OpenGL 初始化失败: {e}", exc_info=True)
            self._initialized = False

    def paintGL(self):
        """绘制 OpenGL"""
        if not self._initialized or self.model is None:
            return

        try:
            live2d.clearBuffer()
            # 更新眼球追踪
            self._update_eye_tracking()
            self.model.Update()
            self.model.Draw()
        except Exception as e:
            logger.error(f"绘制失败: {e}", exc_info=True)

    def _on_animation_tick(self):
        """动画帧更新"""
        self._update_global_eye_target()
        self.update()

    def _update_global_eye_target(self):
        """根据全局鼠标位置更新眼睛目标"""
        from PySide6.QtWidgets import QApplication
        cursor_pos = QApplication.instance().keyboardModifiers()  # 检查应用状态
        global_pos = self.mapToGlobal(self.rect().center())
        
        # 获取全局鼠标位置
        mouse_pos = self.cursor().pos()
        
        # 计算相对于控件中心的位置
        center_x = global_pos.x()
        center_y = global_pos.y()
        
        # 计算偏移量并归一化 (-1 到 1)
        max_distance = 300  # 最大追踪距离
        dx = (mouse_pos.x() - center_x) / max_distance
        dy = -(mouse_pos.y() - center_y) / max_distance  # Y轴翻转
        
        # 限制范围
        self._eye_target_x = max(-1.0, min(1.0, dx))
        self._eye_target_y = max(-1.0, min(1.0, dy))

    def _update_eye_tracking(self):
        """更新眼球追踪 - 平滑移动"""
        if not self.model:
            return
            
        # 平滑插值
        self._eye_current_x += (self._eye_target_x - self._eye_current_x) * self._eye_smoothing
        self._eye_current_y += (self._eye_target_y - self._eye_current_y) * self._eye_smoothing
        
        try:
            # 设置眼球参数
            self.model.SetParameterValue("ParamEyeBallX", self._eye_current_x, 1.0)
            self.model.SetParameterValue("ParamEyeBallY", self._eye_current_y, 1.0)
        except Exception:
            # 某些模型可能不支持这些参数
            pass

    def resizeGL(self, w, h):
        """窗口大小改变"""
        if self.model and w > 0 and h > 0:
            self.model.Resize(w, h)

    def load_model(self, model_path: str):
        """加载 Live2D 模型"""
        if not self._initialized:
            logger.info(f"OpenGL 尚未初始化，延迟加载模型: {model_path}")
            self._pending_model_path = model_path
            return True
        return self._load_model_internal(model_path)

    def _load_model_internal(self, model_path: str):
        """内部加载模型方法"""
        try:
            import json
            logger.info(f"开始加载模型: {model_path}")


            model_path_obj = Path(model_path)
            if not model_path_obj.exists():
                raise FileNotFoundError(f"模型目录不存在: {model_path}")

            model3_files = list(model_path_obj.glob("*.model3.json"))
            if not model3_files:
                raise FileNotFoundError(f"未找到 .model3.json 文件在: {model_path}")

            model_json_path = model3_files[0]
            logger.info(f"找到模型文件: {model_json_path}")

            # 读取模型配置文件，解析 motions
            self._parse_model_motions(model_json_path)

            self.model = live2d.LAppModel()
            self.model.LoadModelJson(str(model_json_path.absolute()))
            logger.info("模型 JSON 加载成功")

            # 尝试获取模型的画布尺寸
            self._detect_model_canvas_size(model_json_path)

            config = get_config()
            # 使用 general.model_scale 作为统一的缩放配置
            self._scale = config.general.model_scale
            self.model.SetScale(self._scale)
            logger.info(f"设置缩放: {self._scale}")

            w, h = self.width(), self.height()
            if w > 0 and h > 0:
                logger.info(f"设置模型画布大小: {w}x{h}")
                self.model.Resize(w, h)
            else:
                QTimer.singleShot(50, self._resize_model)

            self._model_loaded = True
            logger.info(f"模型加载完成，可用动作: {list(self._motion_map.keys())}")
            
            # 通知父控件更新大小
            self._emit_recommended_size()
            
            return True

        except Exception as e:
            logger.error(f"加载模型失败: {e}", exc_info=True)
            return False

    def _detect_model_canvas_size(self, model_json_path: Path):
        """
        检测模型的画布尺寸
        从模型配置中读取或使用默认值
        """
        try:
            import json
            with open(model_json_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 尝试从配置中读取画布尺寸
            # Live2D 模型通常在 Layout 或其他字段中定义画布大小
            layout = config.get("Layout", {})
            
            if layout:
                # 有些模型会定义 CenterX, CenterY, Width, Height
                width = layout.get("Width")
                height = layout.get("Height")
                
                if width and height:
                    # 转换为像素值（Live2D 使用的是归一化坐标）
                    # 通常画布大小在 1000-2000 范围内
                    self._model_natural_width = int(width * 500)
                    self._model_natural_height = int(height * 500)
                    logger.info(f"检测到模型画布尺寸: {self._model_natural_width}x{self._model_natural_height}")
                    return
            
            # 如果没有找到，使用默认值
            logger.info("未找到模型画布尺寸，使用默认值")
            
        except Exception as e:
            logger.warning(f"检测模型画布尺寸失败: {e}")

    def _emit_recommended_size(self):
        """
               根据模型自然尺寸和当前缩放，发出推荐的窗口大小
               """
        # 计算推荐窗口大小
        # 添加边距，让模型不会紧贴窗口边缘
        margin_ratio = -0.3  # 5% 边距

        recommended_width = int(self._model_natural_width * self._scale * (1 + margin_ratio))
        recommended_height = int(self._model_natural_height * self._scale * (1 + margin_ratio))

        logger.info(f"推荐窗口大小: {recommended_width}x{recommended_height}")

        # 发出信号
        self.size_changed.emit(recommended_width, recommended_height)


    def _parse_model_motions(self, model_json_path: Path):
        """从模型配置文件解析动作映射"""
        import json
        try:
            with open(model_json_path, 'r', encoding='utf-8') as f:
                self._model_config = json.load(f)
            
            motions = self._model_config.get("FileReferences", {}).get("Motions", {})
            self._motion_map = {}
            
            # 遍历所有动作组（通常主组是空字符串 ""）
            for group_name, motion_list in motions.items():
                for index, motion_entry in enumerate(motion_list):
                    file_path = motion_entry.get("File", "")
                    # 从文件路径提取动作名称: motions/idle.motion3.json -> idle
                    if file_path:
                        motion_name = Path(file_path).stem  # 去掉目录和扩展名
                        # 去掉 .motion3 后缀（如果有）
                        if motion_name.endswith(".motion3"):
                            motion_name = motion_name[:-8]
                        self._motion_map[motion_name] = index
                        logger.debug(f"解析动作: {motion_name} -> 索引 {index} (组: '{group_name}')")
            
            logger.info(f"从模型解析到 {len(self._motion_map)} 个动作: {list(self._motion_map.keys())}")
            
        except Exception as e:
            logger.error(f"解析模型动作失败: {e}", exc_info=True)
            self._motion_map = {"idle": 0}  # 默认备用

    def get_available_motions(self) -> list:
        """获取模型支持的所有动作名称列表"""
        return list(self._motion_map.keys())

    def _resize_model(self):
        """调整模型画布大小"""
        if self.model:
            w, h = self.width(), self.height()
            if w > 0 and h > 0:
                self.model.Resize(w, h)

    def set_scale(self, scale: float):
        """设置缩放"""
        self._scale = scale
        if self.model:
            self.model.SetScale(scale)
        
        # 发出推荐的窗口大小
        if self._model_loaded:
            self._emit_recommended_size()

    def play_motion(self, motion_name: str):
        """播放动作"""
        if self.model:
            try:
                logger.info(f"播放动作: {motion_name}")
                
                if not self._motion_map:
                    logger.warning("动作映射表为空，无法播放动作")
                    return
                
                motion_no = self._motion_map.get(motion_name)
                if motion_no is None:
                    # 尝试模糊匹配
                    available = list(self._motion_map.keys())
                    logger.warning(f"动作 '{motion_name}' 不在映射表中，可用动作: {available}")
                    # 默认使用第一个动作或 idle
                    motion_no = self._motion_map.get("idle", 0)
                
                self.model.StartMotion("", motion_no, 3)
            except Exception as e:
                logger.error(f"播放动作失败: {e}", exc_info=True)

    def update_mood(self, mood: str):
        """更新心情"""
        if self.model:
            try:
                logger.info(f"更新心情: {mood}")
                if mood == "happy":
                    self.model.SetParameterValue("ParamEyeLOpen", 1.0, 1.0)
                    self.model.SetParameterValue("ParamEyeROpen", 1.0, 1.0)
                elif mood == "sad":
                    self.model.SetParameterValue("ParamEyeLOpen", 0.5, 1.0)
                    self.model.SetParameterValue("ParamEyeROpen", 0.5, 1.0)
            except Exception as e:
                logger.error(f"更新心情失败: {e}", exc_info=True)

    def mousePressEvent(self, event):
        """鼠标按下"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._press_pos = event.position().toPoint()
            self._is_dragging = False
            event.accept()

    def mouseMoveEvent(self, event):
        """鼠标移动"""
        if self._press_pos is not None and not self._is_dragging:
            current_pos = event.position().toPoint()
            # 检查是否超过拖拽阈值
            distance = (current_pos - self._press_pos).manhattanLength()
            if distance > self._drag_threshold:
                # 开始拖拽
                self._is_dragging = True
                global_pos = self.mapToGlobal(self._press_pos)
                self.drag_started.emit(global_pos)
                logger.debug("开始拖拽")
        event.accept()

    def mouseReleaseEvent(self, event):
        """鼠标释放"""
        if event.button() == Qt.MouseButton.LeftButton:
            if not self._is_dragging and self._press_pos is not None:
                # 没有拖拽，视为点击
                self.clicked.emit()
                # 触发模型的 Touch
                if self.model:
                    x = event.position().x()
                    y = event.position().y()
                    try:
                        self.model.Touch(x, y, lambda g, n: None, lambda: None)
                    except Exception:
                        pass
            self._press_pos = None
            self._is_dragging = False
        event.accept()


class Live2DWidget(QFrame):
    """Live2D 桌面宠物控件"""

    clicked = Signal()
    motion_played = Signal(str)
    drag_started = Signal(QPoint)  # 转发拖拽信号
    size_changed = Signal(int, int)  # 转发窗口大小变化信号

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

        # Live2D OpenGL 控件
        self.live2d_widget = Live2DGLWidget()
        self.live2d_widget.setMinimumSize(140, 215)
        self.live2d_widget.clicked.connect(self._on_live2d_clicked)
        self.live2d_widget.drag_started.connect(self.drag_started)
        self.live2d_widget.size_changed.connect(self._on_size_changed)
        layout.addWidget(self.live2d_widget, 1)
        logger.info("使用 Live2D OpenGL 渲染")

        # 透明背景，无边框
        self.setStyleSheet("""
            QFrame {
                background-color: transparent;
            }
        """)
        
        # 设置初始大小（会在模型加载后自动调整）
        self.setFixedSize(350, 500)

    def _load_model(self):
        """加载模型"""
        try:
            config = get_config()
            model_path = config.live2d.model_path
            logger.info(f"Live2D 模型路径: {model_path}")
            QTimer.singleShot(100, self._do_load_model)
        except Exception as e:
            logger.error(f"加载模型时出错: {e}", exc_info=True)

    def _do_load_model(self):
        """实际执行模型加载"""
        try:
            config = get_config()
            model_path = config.live2d.model_path
            self.live2d_widget.load_model(model_path)
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
        # 调整自身大小
        self.setFixedSize(width, height)
        
        # 转发信号给主窗口
        self.size_changed.emit(width, height)
        
        logger.info(f"Live2DWidget 大小调整为: {width}x{height}")

    def play_motion(self, motion_id: str, mood: str = None):
        """播放动作"""
        from live2d_renderer.motion_controller import MotionController
        motion_controller = MotionController()
        settings = motion_controller.config.get("settings", {})
        enable_chat_motion = settings.get("enable_chat_motion", True)

        # 防御性检查：motion_id 为 None 时跳过
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
        # 调用内部控件的缩放方法
        # 大小变化会通过 size_changed 信号传递
        self.live2d_widget.set_scale(scale)
