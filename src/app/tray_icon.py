# System Tray Icon
import sys
from pathlib import Path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import Signal, QObject

from utils import get_logger
from utils.constants import IMAGES_DIR, BUILTIN_ASSETS_DIR

logger = get_logger()


class TrayIcon(QObject):
    """系统托盘图标"""

    show_window = Signal()
    hide_window = Signal()
    toggle_window = Signal()
    open_settings = Signal()
    quit_app = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tray = QSystemTrayIcon(parent)
        self._setup_tray()
        self._setup_menu()

    def _setup_tray(self):
        """设置托盘图标"""
        # 优先从用户目录查找图标，找不到则从项目内置资源查找
        icon_filename = "AI助手.png"
        icon_path = IMAGES_DIR / icon_filename
        if not icon_path.exists():
            icon_path = BUILTIN_ASSETS_DIR / "images" / icon_filename
        
        if icon_path.exists():
            icon = QIcon(str(icon_path))
            self._tray.setIcon(icon)
            logger.info(f"托盘图标已加载: {icon_path}")
        else:
            logger.warning(f"托盘图标文件不存在: {icon_path}")
        
        self._tray.setToolTip("AI Friend - 二次元桌面助手")

        # 连接点击事件
        self._tray.activated.connect(self._on_tray_activated)

    def _setup_menu(self):
        """设置右键菜单"""
        menu = QMenu()

        # 设置
        settings_action = QAction("设置", menu)
        settings_action.triggered.connect(self.open_settings.emit)
        menu.addAction(settings_action)

        menu.addSeparator()

        # 退出
        quit_action = QAction("退出", menu)
        quit_action.triggered.connect(self.quit_app.emit)
        menu.addAction(quit_action)

        self._tray.setContextMenu(menu)

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason):
        """托盘图标点击"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.toggle_window.emit()

    def show(self):
        """显示托盘图标"""
        self._tray.show()
        logger.info("系统托盘已显示")

    def hide(self):
        """隐藏托盘图标"""
        self._tray.hide()

    def is_visible(self) -> bool:
        """是否可见"""
        return self._tray.isVisible()

    def show_message(self, title: str, message: str, icon=QSystemTrayIcon.Information, msecs=3000):
        """显示托盘通知"""
        self._tray.showMessage(title, message, icon, msecs)
