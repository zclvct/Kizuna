#!/usr/bin/env python3
"""
AI Friend - 二次元桌面助手
直接运行入口文件 (避免相对导入问题)
"""
import sys
from pathlib import Path

# 添加 src 到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout,
    QPushButton, QVBoxLayout, QLabel, QFrame,
    QSystemTrayIcon, QMenu, QDialog, QTabWidget,
    QFormLayout, QLineEdit, QComboBox, QCheckBox,
    QSpinBox, QDoubleSpinBox, QTextEdit, QListWidget,
    QListWidgetItem, QFileDialog, QScrollArea
)
from PySide6.QtCore import Qt, QPoint, Signal, QObject, QThread
from PySide6.QtGui import QCursor, QAction

# 简单的日志
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("aiFriend")


class Live2DWidget(QFrame):
    """Live2D 控件占位"""

    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        label = QLabel("🎨 Live2D")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-size: 24px; color: #888;")
        layout.addWidget(label)

        self.setStyleSheet("""
            QFrame {
                background-color: rgba(240, 240, 255, 200);
                border-radius: 10px;
            }
        """)
        self.setFixedSize(300, 400)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()


class ChatWidget(QFrame):
    """对话窗口"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        title = QLabel("💬 对话窗口")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        layout.addWidget(title)

        label = QLabel("对话功能开发中...")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("color: #888; padding: 20px;")
        layout.addWidget(label)

        self.setStyleSheet("""
            ChatWidget {
                background-color: rgba(255, 255, 255, 240);
                border-radius: 12px;
            }
        """)
        self.setFixedWidth(400)


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
        self._toggle_chat_action = QAction("显示对话窗口", self._menu)
        self._toggle_chat_action.triggered.connect(self.toggle_chat.emit)
        self._menu.addAction(self._toggle_chat_action)

        self._menu.addSeparator()

        settings_action = QAction("设置", self._menu)
        settings_action.triggered.connect(self.open_settings.emit)
        self._menu.addAction(settings_action)

        self._menu.addSeparator()

        quit_action = QAction("退出", self._menu)
        quit_action.triggered.connect(self.quit_app.emit)
        self._menu.addAction(quit_action)

    def set_chat_visible(self, visible: bool):
        self._chat_visible = visible
        self._toggle_chat_action.setText("隐藏对话窗口" if visible else "显示对话窗口")

    def exec(self, pos):
        self._menu.exec(pos)


class TrayIcon(QObject):
    """系统托盘"""

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
        self._tray.setToolTip("AI Friend - 二次元桌面助手")
        self._tray.activated.connect(self._on_tray_activated)

    def _setup_menu(self):
        menu = QMenu()

        toggle_action = QAction("显示/隐藏", menu)
        toggle_action.triggered.connect(self.toggle_window.emit)
        menu.addAction(toggle_action)

        menu.addSeparator()

        settings_action = QAction("设置", menu)
        settings_action.triggered.connect(self.open_settings.emit)
        menu.addAction(settings_action)

        menu.addSeparator()

        quit_action = QAction("退出", menu)
        quit_action.triggered.connect(self.quit_app.emit)
        menu.addAction(quit_action)

        self._tray.setContextMenu(menu)

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.toggle_window.emit()

    def show(self):
        self._tray.show()
        logger.info("系统托盘已显示")


class SettingsWindow(QDialog):
    """设置窗口"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._setup_window()

    def _setup_window(self):
        self.setWindowTitle("设置")
        self.setMinimumSize(500, 400)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        tabs = QTabWidget()

        # LLM 标签页
        llm_tab = QWidget()
        llm_layout = QFormLayout(llm_tab)
        llm_layout.addRow("提供商:", QComboBox())
        llm_layout.addRow("模型:", QLineEdit())
        llm_layout.addRow("API Key:", QLineEdit())
        tabs.addTab(llm_tab, "LLM")

        # Live2D 标签页
        live2d_tab = QWidget()
        live2d_layout = QFormLayout(live2d_tab)
        live2d_layout.addRow("模型路径:", QLineEdit())
        live2d_layout.addRow("缩放:", QDoubleSpinBox())
        tabs.addTab(live2d_tab, "Live2D")

        # 角色设定标签页
        char_tab = QWidget()
        char_layout = QFormLayout(char_tab)
        char_layout.addRow("名字:", QLineEdit())
        char_layout.addRow("性格:", QLineEdit())
        tabs.addTab(char_tab, "角色设定")

        # 技能标签页
        skills_tab = QWidget()
        skills_layout = QVBoxLayout(skills_tab)
        skills_layout.addWidget(QLabel("技能配置 (开发中)"))
        tabs.addTab(skills_tab, "技能")

        # 通用标签页
        general_tab = QWidget()
        general_layout = QFormLayout(general_tab)
        general_layout.addRow("开机自启:", QCheckBox())
        general_layout.addRow("窗口置顶:", QCheckBox())
        tabs.addTab(general_tab, "通用")

        layout.addWidget(tabs)

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self._drag_position = None
        self._chat_visible = False
        self._setup_ui()
        self._setup_window_flags()
        self._setup_context_menu()

    def _setup_window_flags(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        self.layout = QHBoxLayout(central)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(10)

        self.live2d_widget = Live2DWidget()
        self.live2d_widget.clicked.connect(self._on_live2d_clicked)
        self.layout.addWidget(self.live2d_widget)

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

        self.chat_widget = ChatWidget()
        self.chat_widget.setVisible(False)
        self.layout.addWidget(self.chat_widget)

        self._update_window_size()

    def _setup_context_menu(self):
        self.context_menu = ContextMenu(self)
        self.context_menu.toggle_chat.connect(self._toggle_chat)
        self.context_menu.open_settings.connect(self._open_settings)
        self.context_menu.quit_app.connect(self.close)

    def _toggle_chat(self):
        self._chat_visible = not self._chat_visible
        self.chat_widget.setVisible(self._chat_visible)
        self.context_menu.set_chat_visible(self._chat_visible)
        self._update_window_size()

    def _update_window_size(self):
        if self._chat_visible:
            self.setFixedSize(720, 420)
        else:
            self.setFixedSize(320, 420)

    def _on_live2d_clicked(self):
        logger.info("Live2D clicked")

    def _open_settings(self):
        dialog = SettingsWindow(self)
        dialog.exec()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self._drag_position and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_position)

    def contextMenuEvent(self, event):
        self.context_menu.exec(QCursor.pos())


def main():
    """主函数"""
    logger.info("=" * 50)
    logger.info("AI Friend - 二次元桌面助手")
    logger.info("=" * 50)

    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    app.setApplicationName("AI Friend")
    app.setQuitOnLastWindowClosed(False)

    window = MainWindow()
    window.show()
    logger.info("主窗口已显示")

    tray = TrayIcon()
    tray.show()

    tray.toggle_window.connect(window.setVisible)
    tray.open_settings.connect(window._open_settings)
    tray.quit_app.connect(app.quit)

    logger.info("应用启动完成")

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
