# Main Window - 桌面宠物主窗口
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGraphicsDropShadowEffect, QApplication, QPushButton, QLabel,
    QSizeGrip
)
from PySide6.QtCore import Qt, QPoint, QTimer, Signal, QRect
from PySide6.QtGui import QCursor, QColor, QPainterPath, QPainter, QPen, QBrush, QFont

import sys
from pathlib import Path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from utils import get_config, get_character_manager, get_logger, set_motion_callback
from chat import ChatWidget
from live2d_renderer import Live2DWidget
from scheduler import TaskManager, get_task_manager
from app.context_menu import ContextMenu
from app.settings_window import SettingsWindow
from app.tasks_window import TasksWindow
from app.widgets.emoji_bubble import EmojiBubble
from agent.tools.mood_tool import set_emoji_callback, get_mood_by_type

logger = get_logger()


class ChatBubbleWindow(QWidget):
    """聊天气泡窗口 - 独立窗口（二次元风格）"""
    
    closed = Signal()  # 窗口关闭信号

    def __init__(self):
        super().__init__()
        flags = (
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._arrow_on_left = True
        self._resizing = False
        self._resize_start_pos = None
        self._resize_start_geometry = None
        self._setup_ui()
        
    def _setup_ui(self):
        """设置 UI - 二次元风格"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 内容容器（带圆角背景）
        content_widget = QWidget()
        content_widget.setObjectName("chatContent")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # 标题栏（包含标题和关闭按钮）
        title_bar = QWidget()
        title_bar.setObjectName("titleBar")
        title_bar.setFixedHeight(40)
        title_bar.setStyleSheet("""
            QWidget#titleBar {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #A8D8FF, stop:0.5 #C8E8FF, stop:1 #FFB8D9);
                border-top-left-radius: 18px;
                border-top-right-radius: 18px;
            }
        """)
        
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(15, 8, 10, 8)
        title_layout.setSpacing(8)
        
        # 标题
        title_label = QLabel("💬 对话")
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title_label.setStyleSheet("""
            color: white;
            background: transparent;
            text-shadow: 0px 1px 2px rgba(0,0,0,0.1);
        """)
        title_layout.addWidget(title_label)
        
        title_layout.addStretch()
        
        # 关闭按钮
        close_btn = QPushButton("✕")
        close_btn.setObjectName("closeBtn")
        close_btn.setFixedSize(28, 28)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.hide)
        close_btn.setStyleSheet("""
            QPushButton#closeBtn {
                background-color: rgba(255, 255, 255, 0.3);
                color: white;
                border: none;
                border-radius: 14px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton#closeBtn:hover {
                background-color: rgba(255, 100, 100, 0.8);
            }
            QPushButton#closeBtn:pressed {
                background-color: rgba(255, 80, 80, 1.0);
            }
        """)
        title_layout.addWidget(close_btn)
        
        content_layout.addWidget(title_bar)
        
        # 聊天内容区域
        chat_container = QWidget()
        chat_container.setStyleSheet("""
            background-color: rgba(255, 255, 255, 250);
            border-bottom-left-radius: 18px;
            border-bottom-right-radius: 18px;
        """)
        chat_layout = QVBoxLayout(chat_container)
        chat_layout.setContentsMargins(10, 5, 10, 10)
        
        self.chat_widget = ChatWidget()
        self.chat_widget.response_received.connect(self._on_response_received)
        chat_layout.addWidget(self.chat_widget)
        
        content_layout.addWidget(chat_container)
        
        main_layout.addWidget(content_widget)
        
        # 设置最小尺寸和默认尺寸（可调整大小）
        self.setMinimumSize(300, 350)
        self.resize(380, 450)
        
        # 窗口阴影
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(150, 200, 255, 80))
        shadow.setOffset(0, 5)
        self.setGraphicsEffect(shadow)
    
    def _on_response_received(self):
        """收到模型回复"""
        pass
    
    def paintEvent(self, event):
        """绘制圆角背景和箭头"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 绘制箭头指向
        painter.setBrush(QBrush(QColor(255, 255, 255, 250)))
        painter.setPen(QPen(QColor(230, 230, 230), 1))
        
        triangle = QPainterPath()
        if self._arrow_on_left:
            triangle.moveTo(0, 55)
            triangle.lineTo(-12, 65)
            triangle.lineTo(0, 75)
        else:
            triangle.moveTo(self.width(), 55)
            triangle.lineTo(self.width() + 12, 65)
            triangle.lineTo(self.width(), 75)
        painter.drawPath(triangle)
        
        # 绘制右下角调整大小的手柄
        grip_size = 16
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        for i in range(3):
            x = self.width() - grip_size + i * 5
            y = self.height() - grip_size + i * 5
            painter.drawLine(x, self.height() - 5, self.width() - 5, y)

    def show_at(self, global_pos: QPoint, arrow_on_left: bool = True):
        """在指定位置显示"""
        self._arrow_on_left = arrow_on_left
        self.move(global_pos)
        self.show()
        self.activateWindow()
    
    def hideEvent(self, event):
        """窗口隐藏事件"""
        super().hideEvent(event)
        # 发出关闭信号，通知主窗口更新状态
        self.closed.emit()
    
    def mousePressEvent(self, event):
        """鼠标按下 - 检查是否在调整大小区域"""
        if event.button() == Qt.MouseButton.LeftButton:
            # 检查是否在右下角调整大小区域
            grip_margin = 20
            if (event.position().x() >= self.width() - grip_margin and
                event.position().y() >= self.height() - grip_margin):
                self._resizing = True
                self._resize_start_pos = event.globalPosition().toPoint()
                self._resize_start_geometry = self.geometry()
                self.setCursor(Qt.CursorShape.SizeFDiagCursor)
                event.accept()
                return
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """鼠标移动 - 调整大小或显示调整光标"""
        grip_margin = 20
        in_grip_area = (event.position().x() >= self.width() - grip_margin and
                        event.position().y() >= self.height() - grip_margin)
        
        if self._resizing and self._resize_start_geometry:
            # 计算新的尺寸
            delta = event.globalPosition().toPoint() - self._resize_start_pos
            new_width = max(self.minimumWidth(), self._resize_start_geometry.width() + delta.x())
            new_height = max(self.minimumHeight(), self._resize_start_geometry.height() + delta.y())
            self.resize(new_width, new_height)
        elif in_grip_area:
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
    
    def mouseReleaseEvent(self, event):
        """鼠标释放 - 结束调整大小"""
        if self._resizing:
            self._resizing = False
            self._resize_start_pos = None
            self._resize_start_geometry = None
            self.setCursor(Qt.CursorShape.ArrowCursor)
        super().mouseReleaseEvent(event)


class MainWindow(QMainWindow):
    """主窗口 - 桌面宠物"""

    def __init__(self):
        super().__init__()
        logger.info("MainWindow.__init__ 开始")
        
        self.config = get_config()
        self.character_manager = get_character_manager()
        self.task_manager = get_task_manager()

        self._drag_position = None
        self._chat_visible = False
        self._dragging = False

        set_motion_callback(self._on_global_motion)
        set_emoji_callback(self._on_show_emoji)
        
        self._setup_window_flags()
        self._setup_ui()
        self._setup_context_menu()
        self._setup_task_manager()

        # 第一次启动时自动显示对话窗口
        if self.character_manager.persona.is_first_run():
            QTimer.singleShot(200, self._show_chat_initial)
    
    def showEvent(self, event):
        """窗口显示事件 - 在此处恢复位置"""
        super().showEvent(event)
        # 首次显示时恢复位置
        if not hasattr(self, '_position_restored'):
            self._position_restored = True
            self._restore_window_position()

    def _show_chat_initial(self):
        """延迟显示聊天窗口"""
        self._show_chat()
        logger.info("第一次启动，自动显示对话窗口")

    def _setup_window_flags(self):
        """设置窗口标志"""
        flags = Qt.WindowType.FramelessWindowHint
        
        # 根据配置设置是否置顶
        if self.config.general.always_on_top:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        
        # 使用 Tool 标志，使窗口不在任务栏/扩展坞显示
        flags |= Qt.WindowType.Tool
        
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # macOS 上设置特殊属性确保窗口行为正确
        if sys.platform == 'darwin':
            self.setAttribute(Qt.WidgetAttribute.WA_MacAlwaysShowToolWindow, True)
    
    def _restore_window_position(self):
        """恢复窗口位置"""
        x = self.config.general.window_x
        y = self.config.general.window_y
        
        logger.info(f"尝试恢复窗口位置: ({x}, {y})")
        
        # 检查保存的位置是否在任意屏幕内
        screens = QApplication.screens()
        target_screen = None
        
        for screen in screens:
            screen_geo = screen.geometry()
            if screen_geo.contains(QPoint(x, y)):
                target_screen = screen
                break
        
        # 如果找不到对应屏幕，使用主屏幕
        if target_screen is None:
            target_screen = QApplication.primaryScreen()
            logger.info(f"位置不在任何屏幕内，使用主屏幕")
        
        # 使用可用区域（排除任务栏/停靠栏）
        available_rect = target_screen.availableGeometry()
        screen_geo = target_screen.geometry()
        
        logger.info(f"目标屏幕可用区域: {available_rect}, 屏幕几何: {screen_geo}")
        
        # 确保窗口在屏幕可见范围内
        # 使用屏幕几何区域作为边界，而不是可用区域（避免位置被过度调整）
        min_x = screen_geo.left()
        max_x = screen_geo.right() - self.width()
        min_y = screen_geo.top()
        max_y = screen_geo.bottom() - self.height()
        
        # 如果保存的位置在可用区域内，直接使用
        # 否则，限制在屏幕边界内
        x = max(min_x, min(x, max_x))
        y = max(min_y, min(y, max_y))
        
        self.move(x, y)
        logger.info(f"窗口位置恢复至: ({x}, {y})")
    
    def _save_window_position(self):
        """保存窗口位置"""
        pos = self.pos()
        self.config.general.window_x = pos.x()
        self.config.general.window_y = pos.y()
        logger.info(f"窗口位置已保存: ({pos.x()}, {pos.y()})")

    def _setup_ui(self):
        """设置 UI"""
        central = QWidget()
        self.setCentralWidget(central)
        central.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(5, 5, 5, 5)

        # Live2D 控件
        self.live2d_widget = Live2DWidget()
        self.live2d_widget.setObjectName("live2dWidget")
        self.live2d_widget.motion_played.connect(self._on_motion_played)
        self.live2d_widget.drag_started.connect(self._on_drag_started)
        layout.addWidget(self.live2d_widget)

        # 聊天气泡 - 独立窗口
        self.chat_bubble = ChatBubbleWindow()
        self.chat_bubble.chat_widget.response_received.connect(self._on_response_received)
        self.chat_bubble.closed.connect(self._on_chat_closed)
        
        # 表情包气泡 - 独立窗口
        self.emoji_bubble = EmojiBubble()
        
        self.setFixedSize(320, 450)

    def _on_drag_started(self, global_pos: QPoint):
        """模型区域开始拖拽"""
        # 检查是否允许拖动
        if not self.config.general.draggable:
            logger.debug("拖动已禁用")
            return
        self._drag_position = global_pos - self.frameGeometry().topLeft()
        self._dragging = True
        self.grabMouse()
        logger.debug("开始拖拽窗口")

    def _setup_context_menu(self):
        """设置右键菜单"""
        self.context_menu = ContextMenu(self)
        self.context_menu.toggle_chat.connect(self._toggle_chat)
        self.context_menu.open_settings.connect(self._open_settings)
        self.context_menu.view_tasks.connect(self._view_tasks)
        self.context_menu.quit_app.connect(self._close_all)

    def _setup_task_manager(self):
        """设置任务管理器"""
        self.task_manager.set_task_executor(self._on_task_execute)
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if loop.is_running():
            asyncio.create_task(self.task_manager.start())
        else:
            logger.info("任务管理器将在主程序启动时启动")

    async def _on_task_execute(self, task):
        """定时任务执行回调"""
        logger.info(f"执行定时任务: {task.task_name}")

        if task.motion_id:
            self.live2d_widget.play_motion(task.motion_id)
        else:
            self.live2d_widget.update_mood("happy")

        if self._chat_visible and hasattr(self.chat_bubble.chat_widget, '_add_message_bubble'):
            self.chat_bubble.chat_widget._add_message_bubble(
                f"📋 定时任务: {task.task_name}\n\n{task.action_prompt}",
                is_user=False
            )

    def _get_available_screen(self):
        """获取当前屏幕的可用区域"""
        screen = QApplication.screenAt(self.geometry().center())
        if screen is None:
            screen = QApplication.primaryScreen()
        return screen.availableGeometry()

    def _calculate_bubble_position(self):
        """计算聊天气泡的最佳位置"""
        model_rect = self.geometry()
        screen_rect = self._get_available_screen()
        bubble_width = self.chat_bubble.width()
        bubble_height = self.chat_bubble.height()
        
        # 默认放在右侧
        bubble_x = model_rect.right() + 15
        bubble_y = model_rect.top() + 30
        arrow_on_left = True
        
        # 检查右侧是否超出屏幕
        if bubble_x + bubble_width > screen_rect.right():
            bubble_x = model_rect.left() - bubble_width - 15
            arrow_on_left = False
        
        if bubble_x < screen_rect.left():
            bubble_x = screen_rect.left()
            arrow_on_left = True
        
        if bubble_y + bubble_height > screen_rect.bottom():
            bubble_y = screen_rect.bottom() - bubble_height - 10
        if bubble_y < screen_rect.top():
            bubble_y = screen_rect.top() + 10
        
        return QPoint(bubble_x, bubble_y), arrow_on_left

    def _show_chat(self):
        """显示聊天窗口"""
        if not self._chat_visible:
            bubble_pos, arrow_left = self._calculate_bubble_position()
            self.chat_bubble.show_at(bubble_pos, arrow_left)
            self._chat_visible = True
            self.context_menu.set_chat_visible(True)
            logger.info("已显示聊天窗口")

    def _hide_chat(self):
        """隐藏聊天窗口"""
        if self._chat_visible:
            self.chat_bubble.hide()
            self._chat_visible = False
            self.context_menu.set_chat_visible(False)
            logger.info("已隐藏聊天窗口")

    def _toggle_chat(self):
        """切换聊天窗口"""
        if self._chat_visible:
            self._hide_chat()
        else:
            self._show_chat()

    def _on_response_received(self):
        """收到模型回复时自动显示聊天窗口"""
        self._show_chat()
    
    def _on_chat_closed(self):
        """聊天窗口被关闭（点击X按钮）"""
        self._chat_visible = False
        self.context_menu.set_chat_visible(False)
        logger.info("聊天窗口已关闭")

    def _update_bubble_position(self):
        """更新气泡位置"""
        if self._chat_visible:
            bubble_pos, arrow_left = self._calculate_bubble_position()
            self.chat_bubble._arrow_on_left = arrow_left
            self.chat_bubble.move(bubble_pos)
            self.chat_bubble.update()

    def _on_global_motion(self, mood: str = None, intent: str = None, motion_id: str = None, new_mood: str = None):
        """全局动作回调"""
        from live2d_renderer.motion_controller import MotionController
        
        if new_mood:
            self.live2d_widget.update_mood(new_mood)

        # 创建 MotionController 实例
        motion_controller = MotionController()
        
        if motion_id:
            self.live2d_widget.play_motion(motion_id)
        elif intent:
            # 根据意图获取动作
            motion = motion_controller.get_motion_for_intent(intent)
            if motion:
                self.live2d_widget.play_motion(motion)
            elif mood:
                # 意图没有对应动作，尝试使用心情
                motion = motion_controller.get_motion_for_mood(mood)
                if motion:
                    self.live2d_widget.play_motion(motion, mood=mood)
        elif mood:
            # 只根据心情获取动作
            motion = motion_controller.get_motion_for_mood(mood)
            if motion:
                self.live2d_widget.play_motion(motion, mood=mood)

    def _on_show_emoji(self, mood: str):
        """显示表情包回调"""
        logger.info(f"_on_show_emoji 被调用: {mood}")
        entry = get_mood_by_type(mood)
        
        if not entry:
            logger.warning(f"未找到类型 {mood} 的表情包配置，请检查 data/moods.json")
            return
        
        # 计算模型头顶位置（全局坐标）
        model_rect = self.geometry()
        
        # 模型头顶位置：窗口中央偏上
        # Live2D 模型通常在窗口中央，头顶约在窗口顶部 20-30% 的位置
        head_x = model_rect.center().x()
        head_y = model_rect.top() + int(model_rect.height() * 0.15)  # 头顶位置
        
        from PySide6.QtCore import QPoint
        model_head_pos = QPoint(head_x, head_y)
        
        logger.info(f"准备显示表情包: {entry.file_path}, 模型头顶位置: {model_head_pos}")
        self.emoji_bubble.show_emoji(
            entry.file_path,
            entry.duration,
            model_head_pos  # 传入模型头顶位置，气泡会显示在上方
        )

    def _on_motion_played(self, motion_id: str):
        """动作播放完成"""
        logger.debug(f"Motion played: {motion_id}")

    def _open_settings(self):
        """打开设置"""
        dialog = SettingsWindow(self)
        # 连接模型变更信号，延迟刷新模型避免 OpenGL 上下文冲突
        dialog.model_changed.connect(self._delayed_model_reload)
        # 连接缩放变更信号
        dialog.scale_changed.connect(self._on_scale_changed)
        # 连接窗口置顶变更信号
        dialog.always_on_top_changed.connect(self._on_always_on_top_changed)
        # 连接拖动状态变更信号
        dialog.draggable_changed.connect(self._on_draggable_changed)
        dialog.exec()
    
    def _on_scale_changed(self, scale: float):
        """模型缩放变化"""
        self.live2d_widget.set_scale(scale)
        logger.info(f"模型缩放更新: {scale}")
    
    def _on_always_on_top_changed(self, always_on_top: bool):
        """窗口置顶状态变化"""
        # 保存当前窗口位置
        pos = self.pos()
        
        # 重新设置窗口标志
        flags = Qt.WindowType.FramelessWindowHint
        if always_on_top:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        
        # 使用 Tool 标志，使窗口不在任务栏/扩展坞显示
        flags |= Qt.WindowType.Tool
        
        self.setWindowFlags(flags)
        
        # macOS 上设置特殊属性
        if sys.platform == 'darwin':
            self.setAttribute(Qt.WidgetAttribute.WA_MacAlwaysShowToolWindow, True)
        
        self.show()
        self.move(pos)
        
        # 更新聊天气泡位置
        if self._chat_visible:
            self._update_bubble_position()
        
        logger.info(f"窗口置顶状态更新: {always_on_top}")
    
    def _on_draggable_changed(self, draggable: bool):
        """拖动状态变化"""
        if not draggable and self._dragging:
            self.releaseMouse()
            self._dragging = False
        logger.info(f"拖动状态更新: {draggable}")

    def _delayed_model_reload(self, model_path: str):
        """延迟重新加载模型"""
        QTimer.singleShot(100, lambda: self._on_model_changed(model_path))


    def _on_model_changed(self, model_path: str):
        """模型变更处理"""
        logger.info(f"重新加载模型: {model_path}")
        # 重新加载 Live2D 模型
        self.live2d_widget.live2d_widget.load_model(model_path)
        # 清除动作缓存，让 motion_tool 重新读取
        from live2d_renderer.motion_controller import MotionController
        MotionController().clear_motions_cache()
        logger.info("模型和动作缓存已更新")

    def _view_tasks(self):
        """查看定时任务"""
        dialog = TasksWindow(self)
        dialog.exec()

    def _close_all(self):
        """关闭所有窗口并退出应用"""
        # 保存窗口位置和配置
        self._save_window_position()
        self.config.save()
        
        self.chat_bubble.close()
        self.emoji_bubble.close()
        self.close()
        
        # 退出应用
        QApplication.instance().quit()

    def mouseMoveEvent(self, event):
        """鼠标移动 - 拖拽窗口"""
        if self._dragging and self._drag_position:
            new_pos = event.globalPosition().toPoint() - self._drag_position
            self.move(new_pos)
            self._update_bubble_position()
            event.accept()

    def mouseReleaseEvent(self, event):
        """鼠标释放"""
        if self._dragging:
            self.releaseMouse()
            logger.debug("结束拖拽窗口")
            # 拖动结束后立即保存位置
            self._save_window_position()
            self.config.save()
        self._drag_position = None
        self._dragging = False

    def contextMenuEvent(self, event):
        """右键菜单"""
        self.context_menu.exec(QCursor.pos())

    def closeEvent(self, event):
        """关闭窗口"""
        # 保存窗口位置
        self._save_window_position()
        self.config.save()
        
        self.chat_bubble.close()
        self.emoji_bubble.close()
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self.task_manager.stop())
        except:
            pass
        event.accept()
