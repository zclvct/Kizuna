# Live2D Widget - 使用 live2d-py
import sys
from pathlib import Path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel
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

    def __init__(self, parent=None):
        super().__init__(parent)
        self.model = None
        self._scale = 1.0
        self._initialized = False
        self._model_loaded = False
        self._pending_model_path = None
        
        # 拖拽相关
        self._press_pos = None  # 按下时的位置
        self._is_dragging = False
        self._drag_threshold = 5  # 拖拽阈值（像素）
        
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
        self._animation_timer.timeout.connect(self.update)
        self._animation_timer.start(16)
        
        # 设置鼠标追踪
        self.setMouseTracking(True)

    def initializeGL(self):
        """初始化 OpenGL"""
        logger.info("初始化 OpenGL...")
        try:
            live2d.init()
            live2d.glInit()
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
            self.model.Update()
            self.model.Draw()
        except Exception as e:
            logger.error(f"绘制失败: {e}", exc_info=True)

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
            logger.info(f"开始加载模型: {model_path}")

            model_path_obj = Path(model_path)
            if not model_path_obj.exists():
                raise FileNotFoundError(f"模型目录不存在: {model_path}")

            model3_files = list(model_path_obj.glob("*.model3.json"))
            if not model3_files:
                raise FileNotFoundError(f"未找到 .model3.json 文件在: {model_path}")

            model_json_path = model3_files[0]
            logger.info(f"找到模型文件: {model_json_path}")

            self.model = live2d.LAppModel()
            self.model.LoadModelJson(str(model_json_path.absolute()))
            logger.info("模型 JSON 加载成功")

            config = get_config()
            self._scale = config.live2d.scale
            self.model.SetScale(self._scale)
            logger.info(f"设置缩放: {self._scale}")

            w, h = self.width(), self.height()
            if w > 0 and h > 0:
                logger.info(f"设置模型画布大小: {w}x{h}")
                self.model.Resize(w, h)
            else:
                QTimer.singleShot(50, self._resize_model)

            self._model_loaded = True
            logger.info("模型加载完成")
            return True

        except Exception as e:
            logger.error(f"加载模型失败: {e}", exc_info=True)
            return False

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

    def play_motion(self, motion_name: str):
        """播放动作"""
        if self.model:
            try:
                logger.info(f"播放动作: {motion_name}")
                motion_map = {
                    'complete': 0, 'home': 1, 'idle': 2, 'login': 3, 'mail': 4,
                    'main_1': 5, 'main_2': 6, 'main_3': 7, 'mission_complete': 8,
                    'mission': 9, 'touch_body': 10, 'touch_head': 11,
                    'touch_special': 12, 'wedding': 13,
                }
                motion_no = motion_map.get(motion_name, 2)
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
        self.live2d_widget.setMinimumSize(280, 380)
        self.live2d_widget.clicked.connect(self._on_live2d_clicked)
        self.live2d_widget.drag_started.connect(self.drag_started)  # 转发拖拽信号
        layout.addWidget(self.live2d_widget, 1)
        logger.info("使用 Live2D OpenGL 渲染")

        # 名称标签 - 小巧美观
        self.name_label = QLabel()
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                font-weight: bold;
                color: #333;
                background-color: rgba(255, 255, 255, 180);
                border-radius: 8px;
                padding: 3px 12px;
            }
        """)
        layout.addWidget(self.name_label, 0, Qt.AlignmentFlag.AlignCenter)

        # 透明背景，无边框
        self.setStyleSheet("""
            QFrame {
                background-color: transparent;
            }
        """)
        self.setFixedSize(300, 430)

        self._update_info_display()

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
            success = self.live2d_widget.load_model(model_path)
            if success:
                persona = self.character_manager.persona
                self.name_label.setText(persona.name)
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

    def _update_info_display(self):
        """更新信息显示"""
        persona = self.character_manager.persona
        self.name_label.setText(persona.name)

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

    def play_motion(self, motion_id: str, mood: str = None):
        """播放动作"""
        from live2d_renderer.motion_controller import MotionController
        motion_controller = MotionController()
        settings = motion_controller.config.get("settings", {})
        enable_chat_motion = settings.get("enable_chat_motion", True)

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
