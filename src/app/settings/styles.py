# Styles - 二次元风格样式

# 主样式
ANIME_STYLE = """
QDialog {
    background-color: #f6f9ff;
}
QTabWidget::pane {
    border: 1px solid #dce8ff;
    border-radius: 12px;
    background-color: rgba(255, 255, 255, 0.96);
}
QTabBar::tab {
    background-color: #edf3ff;
    color: #5c6b86;
    padding: 9px 18px;
    margin-right: 4px;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
    font-weight: 600;
    min-width: 84px;
}
QTabBar::tab:selected {
    background-color: white;
    color: #4f7dff;
    border-bottom: 2px solid white;
}
QTabBar::tab:hover:!selected {
    background-color: #e4efff;
    color: #4f7dff;
}
QPushButton {
    background-color: #5c9eff;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 8px 18px;
    font-weight: 600;
    min-width: 72px;
}
QPushButton:hover {
    background-color: #4a8ae5;
}
QPushButton:pressed {
    background-color: #3d7ad1;
}
QPushButton:disabled {
    background-color: #cfd9ea;
    color: #8b97ad;
}
QPushButton#secondaryBtn {
    background-color: #f0f0f0;
    color: #666;
}
QPushButton#secondaryBtn:hover {
    background-color: #e0e0e0;
}
QLineEdit, QTextEdit {
    border: 1px solid #d6e2f5;
    border-radius: 8px;
    padding: 7px 10px;
    background-color: white;
}
QLineEdit:focus, QTextEdit:focus {
    border-color: #5c9eff;
    background-color: #fafdff;
}
QSpinBox, QDoubleSpinBox {
    border: 2px solid #e0e0e0;
    border-radius: 6px;
    padding: 4px 8px;
    background-color: white;
    padding-right: 20px;
}
QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #5c9eff;
}
QSpinBox::up-button, QDoubleSpinBox::up-button,
QSpinBox::down-button, QDoubleSpinBox::down-button {
    width: 20px;
    border: none;
    background-color: #f0f0f0;
}
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
    background-color: #e0e0e0;
}
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {
    image: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxMCIgaGVpZ2h0PSIxMCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiM2NjYiIHN0cm9rZS13aWR0aD0iMiI+PHBhdGggZD0iTTE4IDE1bC02LTYtNiA2Ii8+PC9zdmc+);
    width: 12px;
    height: 12px;
}
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {
    image: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxMCIgaGVpZ2h0PSIxMCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiM2NjYiIHN0cm9rZS13aWR0aD0iMiI+PHBhdGggZD0iTTYgOWw2IDYgNi02Ii8+PC9zdmc+);
    width: 12px;
    height: 12px;
}
QLabel {
    color: #333;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 2px solid #ccc;
    background-color: white;
}
QCheckBox::indicator:checked {
    background-color: #5c9eff;
    border-color: #5c9eff;
}
QCheckBox::indicator:unchecked {
    background-color: white;
    border-color: #ccc;
}
QCheckBox::indicator:unchecked:hover {
    border-color: #5c9eff;
    background-color: #f0f7ff;
}
QGroupBox {
    border: 2px solid #e0e0e0;
    border-radius: 8px;
    margin-top: 10px;
    padding-top: 10px;
    font-weight: bold;
    color: #333;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
}
QScrollArea {
    border: none;
}
QListWidget {
    border: 2px solid #e0e0e0;
    border-radius: 8px;
    background-color: white;
}
QListWidget::item {
    padding: 10px;
    border-bottom: 1px solid #f0f0f0;
}
QListWidget::item:selected {
    background-color: #e8f4ff;
    color: #333;
}
"""

# 下拉框样式 - 更美观
COMBO_BOX_STYLE = """
QComboBox {
    border: 2px solid #e0e0e0;
    border-radius: 6px;
    padding: 6px 10px;
    background-color: white;
    min-width: 100px;
}
QComboBox:hover {
    border-color: #5c9eff;
}
QComboBox:focus {
    border-color: #5c9eff;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
    background: transparent;
}
QComboBox::down-arrow {
    image: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxMCIgaGVpZ2h0PSIxMCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiM2NjYiIHN0cm9rZS13aWR0aD0iMiI+PHBhdGggZD0iTTYgOWw2IDYgNi02Ii8+PC9zdmc+);
    width: 14px;
    height: 14px;
}
QComboBox QAbstractItemView {
    border: 2px solid #e0e0e0;
    border-radius: 8px;
    background-color: white;
    selection-background-color: #e8f4ff;
    selection-color: #333;
    padding: 4px;
}
QComboBox QAbstractItemView::item {
    padding: 6px 10px;
    border-radius: 4px;
    min-height: 24px;
}
QComboBox QAbstractItemView::item:hover {
    background-color: #f0f7ff;
}
QComboBox QAbstractItemView::item:selected {
    background-color: #e8f4ff;
    color: #333;
}
"""

# 卡片样式
CARD_STYLE = """
QFrame#card {
    background-color: white;
    border: 2px solid #e0e0e0;
    border-radius: 12px;
}
QFrame#card:hover {
    border-color: #5c9eff;
    background-color: #f8fbff;
}
QFrame#cardDefault {
    background-color: white;
    border: 3px solid #5c9eff;
    border-radius: 12px;
}
QFrame#cardDefault:hover {
    background-color: #f0f7ff;
}
QFrame#addCard {
    background-color: #f0f0f0;
    border: 2px dashed #ccc;
    border-radius: 12px;
}
QFrame#addCard:hover {
    background-color: #e8f4ff;
    border-color: #5c9eff;
}
"""

# 菜单样式
MENU_STYLE = """
QMenu {
    background-color: #ffffff;
    border: 1px solid #dce8ff;
    border-radius: 10px;
    padding: 6px;
}
QMenu::item {
    padding: 8px 18px;
    border-radius: 6px;
    margin: 2px;
    color: #44506a;
}
QMenu::item:selected {
    background-color: #e9f2ff;
    color: #2f5fd8;
}
QMenu::item:disabled {
    color: #a4afc3;
}
QMenu::icon {
    padding-left: 6px;
}
QMenu::separator {
    height: 1px;
    background-color: #e6eefc;
    margin: 5px 8px;
}
"""
