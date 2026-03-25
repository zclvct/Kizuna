# Message Bubble Widget - 二次元风格
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QColor


class MessageBubble(QWidget):
    """消息气泡 - 二次元可爱风格"""

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
        """设置 UI - 二次元风格"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        # 气泡容器
        bubble = QWidget()
        bubble_layout = QVBoxLayout(bubble)
        bubble_layout.setContentsMargins(14, 10, 14, 10)
        bubble_layout.setSpacing(4)

        # 消息文本
        self._label = QLabel(self._text)
        self._label.setWordWrap(True)
        self._label.setTextFormat(Qt.TextFormat.MarkdownText)
        self._label.setFont(QFont("Arial", 11))
        self._label.setMaximumWidth(280)  # 限制最大宽度

        bubble_layout.addWidget(self._label)

        # 二次元风格样式
        if self._is_user:
            # 用户消息：渐变蓝色气泡
            bubble.setStyleSheet("""
                QWidget {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #A8D8FF, stop:1 #7BB8FF);
                    border-radius: 16px;
                    border-top-right-radius: 4px;
                }
                QLabel {
                    color: white;
                    background-color: transparent;
                    line-height: 1.5;
                }
            """)
            layout.addStretch()
            layout.addWidget(bubble)
        else:
            # AI 消息：柔和的粉白色气泡
            bubble.setStyleSheet("""
                QWidget {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #FFFFFF, stop:1 #FFF5F8);
                    border: 1px solid #FFE8F0;
                    border-radius: 16px;
                    border-top-left-radius: 4px;
                }
                QLabel {
                    color: #555;
                    background-color: transparent;
                    line-height: 1.5;
                }
            """)
            layout.addWidget(bubble)
            layout.addStretch()
        
        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(8)
        shadow.setColor(QColor(0, 0, 0, 25))
        shadow.setOffset(0, 2)
        bubble.setGraphicsEffect(shadow)
