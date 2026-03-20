# Message Bubble Widget
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont


class MessageBubble(QWidget):
    """消息气泡"""

    def __init__(self, text: str, is_user: bool = False, parent=None):
        super().__init__(parent)
        self._text = text
        self._is_user = is_user
        self._label = None
        self._setup_ui()

    def update_text(self, text: str):
        """更新文本（用于流式输出）"""
        self._text = text
        if self._label:
            self._label.setText(text)

    def _setup_ui(self):
        """设置 UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)

        # 气泡
        bubble = QWidget()
        bubble_layout = QVBoxLayout(bubble)
        bubble_layout.setContentsMargins(15, 10, 15, 10)

        self._label = QLabel(self._text)
        self._label.setWordWrap(True)
        self._label.setTextFormat(Qt.TextFormat.MarkdownText)
        self._label.setFont(QFont("Arial", 12))

        bubble_layout.addWidget(self._label)

        # 样式
        if self._is_user:
            bubble.setStyleSheet("""
                QWidget {
                    background-color: #007AFF;
                    border-radius: 18px;
                    border-top-right-radius: 4px;
                }
                QLabel {
                    color: white;
                    background-color: transparent;
                }
            """)
            layout.addStretch()
            layout.addWidget(bubble)
        else:
            bubble.setStyleSheet("""
                QWidget {
                    background-color: #E9E9EB;
                    border-radius: 18px;
                    border-top-left-radius: 4px;
                }
                QLabel {
                    color: black;
                    background-color: transparent;
                }
            """)
            layout.addWidget(bubble)
            layout.addStretch()
