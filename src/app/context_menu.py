# Context Menu
import sys
from pathlib import Path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from PySide6.QtWidgets import QMenu
from PySide6.QtGui import QAction
from PySide6.QtCore import Signal, QObject

from utils import get_logger
from app.settings.styles import MENU_STYLE

logger = get_logger()


class ContextMenu(QObject):
    """右键菜单"""

    toggle_chat = Signal()
    draggable_changed = Signal(bool)
    always_on_top_changed = Signal(bool)
    model_random_motion = Signal()
    model_idle_motion = Signal()
    model_touch_head_motion = Signal()
    model_touch_body_motion = Signal()
    model_switch_outfit_selected = Signal(str)
    model_switch_random = Signal()
    model_reload = Signal()
    open_settings = Signal()
    view_tasks = Signal()
    quit_app = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._menu = QMenu(parent)
        self._menu.setStyleSheet(MENU_STYLE)
        self._chat_visible = False
        self._setup_menu()

    def _setup_menu(self):
        """设置菜单"""
        # 显示/隐藏对话窗口
        self._toggle_chat_action = QAction("💬 显示对话窗口", self._menu)
        self._toggle_chat_action.triggered.connect(self.toggle_chat.emit)
        self._menu.addAction(self._toggle_chat_action)

        # 允许拖动
        self._draggable_action = QAction("🖱️ 允许拖动", self._menu)
        self._draggable_action.setCheckable(True)
        self._draggable_action.toggled.connect(self.draggable_changed.emit)
        self._menu.addAction(self._draggable_action)

        # 窗口置顶
        self._always_on_top_action = QAction("📌 窗口置顶", self._menu)
        self._always_on_top_action.setCheckable(True)
        self._always_on_top_action.toggled.connect(self.always_on_top_changed.emit)
        self._menu.addAction(self._always_on_top_action)

        # 模型二级菜单（参考常见 Web Live2D 菜单）
        model_menu = self._menu.addMenu("🎭 模型")

        random_action = QAction("🎲 随机动作", model_menu)
        random_action.triggered.connect(self.model_random_motion.emit)
        model_menu.addAction(random_action)

        idle_action = QAction("🧘 待机动作", model_menu)
        idle_action.triggered.connect(self.model_idle_motion.emit)
        model_menu.addAction(idle_action)

        touch_head_action = QAction("🤲 摸头", model_menu)
        touch_head_action.triggered.connect(self.model_touch_head_motion.emit)
        model_menu.addAction(touch_head_action)

        touch_body_action = QAction("🙌 摸身体", model_menu)
        touch_body_action.triggered.connect(self.model_touch_body_motion.emit)
        model_menu.addAction(touch_body_action)

        model_menu.addSeparator()

        self._outfit_menu = model_menu.addMenu("👗 换装列表")
        self.set_outfit_list([])

        switch_random_action = QAction("🔀 随机切换模型", model_menu)
        switch_random_action.triggered.connect(self.model_switch_random.emit)
        model_menu.addAction(switch_random_action)

        model_menu.addSeparator()

        reload_action = QAction("♻️ 重新加载模型", model_menu)
        reload_action.triggered.connect(self.model_reload.emit)
        model_menu.addAction(reload_action)

        self._menu.addSeparator()

        # 打开设置
        settings_action = QAction("⚙️ 打开设置", self._menu)
        settings_action.triggered.connect(self.open_settings.emit)
        self._menu.addAction(settings_action)

        # 查看任务
        tasks_action = QAction("⏰ 查看任务", self._menu)
        tasks_action.triggered.connect(self.view_tasks.emit)
        self._menu.addAction(tasks_action)

        self._menu.addSeparator()

        # 退出
        quit_action = QAction("🚪 退出", self._menu)
        quit_action.triggered.connect(self.quit_app.emit)
        self._menu.addAction(quit_action)

    def set_chat_visible(self, visible: bool):
        """设置对话窗口可见状态"""
        self._chat_visible = visible
        if visible:
            self._toggle_chat_action.setText("💬 隐藏对话窗口")
        else:
            self._toggle_chat_action.setText("💬 显示对话窗口")

    def set_draggable(self, draggable: bool):
        """设置允许拖动状态"""
        self._draggable_action.blockSignals(True)
        self._draggable_action.setChecked(draggable)
        self._draggable_action.blockSignals(False)

    def set_always_on_top(self, always_on_top: bool):
        """设置窗口置顶状态"""
        self._always_on_top_action.blockSignals(True)
        self._always_on_top_action.setChecked(always_on_top)
        self._always_on_top_action.blockSignals(False)

    def set_outfit_list(self, outfits: list[str]):
        """设置换装列表（二级菜单）"""
        self._outfit_menu.clear()

        if not outfits:
            empty_action = QAction("（当前模型无可用换装）", self._outfit_menu)
            empty_action.setEnabled(False)
            self._outfit_menu.addAction(empty_action)
            return

        for outfit in outfits:
            action = QAction(str(outfit), self._outfit_menu)
            action.triggered.connect(lambda checked=False, name=str(outfit): self.model_switch_outfit_selected.emit(name))
            self._outfit_menu.addAction(action)

    def exec(self, pos):
        """显示菜单"""
        self._menu.exec(pos)
