# Main Window
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout,
    QPushButton, QVBoxLayout
)
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QCursor

import sys
from pathlib import Path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from utils import get_config, get_character_manager, get_logger, set_motion_callback
from chat import ChatWidget
from live2d import Live2DWidget
from scheduler import TaskManager, get_task_manager
from app.context_menu import ContextMenu
from app.settings_window import SettingsWindow
from app.tasks_window import TasksWindow

logger = get_logger()


class MainWindow(QMainWindow):
    """主窗口 - 整合 Live2D + 对话 + 定时任务"""

    def __init__(self):
        super().__init__()
        self.config = get_config()
        self.character_manager = get_character_manager()
        self.task_manager = get_task_manager()

        self._drag_position = None
        self._chat_visible = False

        # 设置全局动作回调
        set_motion_callback(self._on_global_motion)

        self._setup_ui()
        self._setup_window_flags()
        self._setup_context_menu()
        self._setup_task_manager()

    def _setup_window_flags(self):
        """设置窗口标志"""
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def _setup_ui(self):
        """设置 UI"""
        central = QWidget()
        self.setCentralWidget(central)

        # 布局
        self.layout = QHBoxLayout(central)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(10)

        # Live2D 控件
        self.live2d_widget = Live2DWidget()
        self.live2d_widget.clicked.connect(self._on_live2d_clicked)
        self.live2d_widget.motion_played.connect(self._on_motion_played)
        self.layout.addWidget(self.live2d_widget)

        # 对话按钮 (悬浮在 Live2D 上)
        self.toggle_button = QPushButton("💬", self.live2d_widget)
        self.toggle_button.setGeometry(250, 350, 40, 40)
        self.toggle_button.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border-radius: 20px;
                font-size: 18px;
            }
            QPushButton:hover {
                background-color: #0056CC;
            }
        """)
        self.toggle_button.clicked.connect(self._toggle_chat)

        # 对话窗口
        self.chat_widget = ChatWidget()
        self.chat_widget.setVisible(False)
        self.layout.addWidget(self.chat_widget)

        # 调整窗口大小
        self._update_window_size()

    def _setup_context_menu(self):
        """设置右键菜单"""
        self.context_menu = ContextMenu(self)
        self.context_menu.toggle_chat.connect(self._toggle_chat)
        self.context_menu.open_settings.connect(self._open_settings)
        self.context_menu.view_tasks.connect(self._view_tasks)
        self.context_menu.quit_app.connect(self.close)

    def _setup_task_manager(self):
        """设置任务管理器"""
        # 设置任务执行回调
        self.task_manager.set_task_executor(self._on_task_execute)

        # 启动任务管理器
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if loop.is_running():
            # 如果事件循环已在运行，创建任务
            asyncio.create_task(self.task_manager.start())
        else:
            # 否则在单独线程中启动（这里简化处理，先不启动，等主程序启动）
            logger.info("任务管理器将在主程序启动时启动")

    async def _on_task_execute(self, task):
        """定时任务执行回调"""
        logger.info(f"执行定时任务: {task.task_name}")

        # 更新 Live2D 心情和动作
        if task.motion_id:
            self.live2d_widget.play_motion(task.motion_id)
        else:
            self.live2d_widget.update_mood("happy")

        # 如果对话窗口可见，在对话中显示任务结果
        if self._chat_visible and hasattr(self.chat_widget, '_add_message_bubble'):
            self.chat_widget._add_message_bubble(
                f"📋 定时任务执行: {task.task_name}\n\n{task.action_prompt}",
                is_user=False
            )

    def _toggle_chat(self):
        """切换对话窗口"""
        self._chat_visible = not self._chat_visible
        self.chat_widget.setVisible(self._chat_visible)
        self.context_menu.set_chat_visible(self._chat_visible)
        self._update_window_size()

        if self._chat_visible:
            logger.info("已显示对话窗口")
        else:
            logger.info("已隐藏对话窗口")

    def _update_window_size(self):
        """更新窗口大小"""
        if self._chat_visible:
            self.setFixedSize(720, 420)
        else:
            self.setFixedSize(320, 420)

    def _on_global_motion(self, mood: str = None, intent: str = None, motion_id: str = None, new_mood: str = None):
        """全局动作回调（从工具调用）"""
        if new_mood:
            self.live2d_widget.update_mood(new_mood)

        if motion_id:
            self.live2d_widget.play_motion(motion_id)
        elif mood:
            # 根据心情播放动作
            self.live2d_widget.play_motion(motion_id=motion_id, mood=mood)
        elif intent:
            # 根据意图播放动作
            motion = self.live2d_widget.motion_controller.get_motion_for_intent(intent)
            if motion:
                self.live2d_widget.play_motion(motion)

    def _on_live2d_clicked(self):
        """点击 Live2D"""
        logger.info("Live2D clicked")

    def _on_motion_played(self, motion_id: str):
        """动作播放完成"""
        logger.debug(f"Motion played: {motion_id}")

    def _open_settings(self):
        """打开设置"""
        dialog = SettingsWindow(self)
        dialog.exec()

    def _view_tasks(self):
        """查看定时任务"""
        dialog = TasksWindow(self)
        dialog.exec()

    def mousePressEvent(self, event):
        """鼠标按下 - 开始拖拽"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        """鼠标移动 - 拖拽窗口"""
        if self._drag_position and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_position)

    def contextMenuEvent(self, event):
        """右键菜单"""
        self.context_menu.exec(QCursor.pos())

    def closeEvent(self, event):
        """关闭窗口时停止任务管理器"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self.task_manager.stop())
        except:
            pass
        event.accept()

