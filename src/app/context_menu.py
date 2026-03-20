# Context Menu
import sys
from pathlib import Path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from PySide6.QtWidgets import QMenu
from PySide6.QtGui import QAction
from PySide6.QtCore import Signal, QObject

from utils import get_logger

logger = get_logger()


class ContextMenu(QObject):
    """右键菜单"""

    toggle_chat = Signal()
    open_settings = Signal()
    view_tasks = Signal()
    quit_app = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._menu = QMenu(parent)
        self._chat_visible = False
        self._setup_menu()

    def _setup_menu(self):
        """设置菜单"""
        # 显示/隐藏对话窗口
        self._toggle_chat_action = QAction("显示对话窗口", self._menu)
        self._toggle_chat_action.triggered.connect(self.toggle_chat.emit)
        self._menu.addAction(self._toggle_chat_action)

        self._menu.addSeparator()

        # 设置
        settings_action = QAction("设置", self._menu)
        settings_action.triggered.connect(self.open_settings.emit)
        self._menu.addAction(settings_action)

        # 查看定时任务
        tasks_action = QAction("查看定时任务", self._menu)
        tasks_action.triggered.connect(self.view_tasks.emit)
        self._menu.addAction(tasks_action)

        self._menu.addSeparator()

        # 退出
        quit_action = QAction("退出", self._menu)
        quit_action.triggered.connect(self.quit_app.emit)
        self._menu.addAction(quit_action)

    def set_chat_visible(self, visible: bool):
        """设置对话窗口可见状态"""
        self._chat_visible = visible
        if visible:
            self._toggle_chat_action.setText("隐藏对话窗口")
        else:
            self._toggle_chat_action.setText("显示对话窗口")

    def exec(self, pos):
        """显示菜单"""
        self._menu.exec(pos)
