# Debug Bubble Widget - 可折叠的调试信息气泡（支持文本选择复制）
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QTextBrowser, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QColor

from chat.markdown_renderer import render_markdown, DEBUG_CSS


class DebugBubble(QWidget):
    """可折叠的调试信息气泡 — 内容可选择复制"""

    def __init__(self, debug_type: str, title: str, content: str, parent=None):
        super().__init__(parent)
        self._debug_type = debug_type
        self._title = title
        self._content = content
        self._expanded = False
        self._content_widget = None
        self._browser = None
        self._animation = None
        self._setup_ui()

    def _setup_ui(self):
        """设置 UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 2, 8, 2)
        main_layout.setSpacing(0)

        # ── 标题栏（可点击折叠）──
        header = QWidget()
        header.setCursor(Qt.CursorShape.PointingHandCursor)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 6, 12, 6)
        header_layout.setSpacing(6)

        # 展开/折叠箭头
        self._toggle_icon = QLabel("▶")
        self._toggle_icon.setFixedWidth(12)
        self._toggle_icon.setStyleSheet("color: #888; font-size: 9px;")
        header_layout.addWidget(self._toggle_icon)

        # 类型图标
        icon_label = QLabel(self._get_icon())
        icon_label.setStyleSheet("font-size: 13px;")
        header_layout.addWidget(icon_label)

        # 标题
        title_label = QLabel(self._title)
        title_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: {self._get_title_color()};")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # 复制按钮
        copy_btn = QPushButton("复制")
        copy_btn.setFixedSize(40, 22)
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.setStyleSheet("""
            QPushButton {
                background: rgba(0,0,0,0.05);
                border: 1px solid rgba(0,0,0,0.1);
                border-radius: 4px;
                color: #888;
                font-size: 10px;
            }
            QPushButton:hover {
                background: rgba(0,0,0,0.1);
                color: #555;
            }
        """)
        copy_btn.clicked.connect(self._copy_content)
        header_layout.addWidget(copy_btn)

        # 标题栏样式
        header.setStyleSheet(f"""
            QWidget {{
                background-color: {self._get_header_bg()};
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                border-bottom-left-radius: 8px;
                border-bottom-right-radius: 8px;
            }}
            QWidget:hover {{
                background-color: {self._get_header_bg(hover=True)};
            }}
        """)

        main_layout.addWidget(header)

        # ── 内容区域（默认折叠）──
        self._content_widget = QFrame()
        self._content_widget.setStyleSheet(f"""
            QFrame {{
                background-color: {self._get_content_bg()};
                border-bottom-left-radius: 8px;
                border-bottom-right-radius: 8px;
            }}
        """)

        content_layout = QVBoxLayout(self._content_widget)
        content_layout.setContentsMargins(10, 6, 10, 6)

        # 使用 QTextBrowser 替代 QLabel，支持选择/复制
        self._browser = QTextBrowser()
        self._browser.setReadOnly(True)
        self._browser.setOpenExternalLinks(True)
        self._browser.setFrameShape(QTextBrowser.Shape.NoFrame)
        self._browser.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._browser.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._browser.setMaximumHeight(400)
        self._browser.setStyleSheet("""
            QTextBrowser {
                background: transparent;
                border: none;
                padding: 0;
                selection-background-color: #a8d8ff;
                selection-color: #333;
            }
        """)

        # 渲染内容为 HTML
        html = render_markdown(self._content)
        self._browser.setHtml(
            f"<html><head><style>{DEBUG_CSS}</style></head><body>{html}</body></html>"
        )
        content_layout.addWidget(self._browser)

        # 初始折叠
        self._content_widget.setMaximumHeight(0)
        self._content_widget.setVisible(False)
        main_layout.addWidget(self._content_widget)

        # 点击标题栏切换
        header.mousePressEvent = lambda e: self._toggle_expand()

        # 阴影
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(4)
        shadow.setColor(QColor(0, 0, 0, 15))
        shadow.setOffset(0, 1)
        self.setGraphicsEffect(shadow)

    def _copy_content(self):
        """复制内容到剪贴板"""
        from PySide6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(self._content)

    def _get_icon(self) -> str:
        icons = {
            "tool_call": "🔧",
            "request": "📤",
            "response": "📥",
            "thought": "💭",
        }
        return icons.get(self._debug_type, "📋")

    def _get_title_color(self) -> str:
        colors = {
            "tool_call": "#5c9eff",
            "request": "#ff9800",
            "response": "#4caf50",
            "thought": "#9c27b0",
        }
        return colors.get(self._debug_type, "#666")

    def _get_header_bg(self, hover: bool = False) -> str:
        colors = {
            "tool_call": "#e3f2fd" if not hover else "#bbdefb",
            "request": "#fff3e0" if not hover else "#ffe0b2",
            "response": "#e8f5e9" if not hover else "#c8e6c9",
            "thought": "#f3e5f5" if not hover else "#e1bee7",
        }
        return colors.get(self._debug_type, "#f5f5f5")

    def _get_content_bg(self) -> str:
        colors = {
            "tool_call": "#fafafa",
            "request": "#fffde7",
            "response": "#f1f8e9",
            "thought": "#fce4ec",
        }
        return colors.get(self._debug_type, "#fafafa")

    def _toggle_expand(self):
        """切换展开/折叠"""
        self._expanded = not self._expanded

        if self._expanded:
            self._toggle_icon.setText("▼")
            self._content_widget.setVisible(True)

            # 计算展开高度
            doc_height = self._browser.document().size().height()
            expand_height = min(doc_height + 20, 420)

            self._animation = QPropertyAnimation(self._content_widget, b"maximumHeight")
            self._animation.setDuration(150)
            self._animation.setStartValue(0)
            self._animation.setEndValue(expand_height)
            self._animation.setEasingCurve(QEasingCurve.Type.OutQuad)
            self._animation.start()
        else:
            self._toggle_icon.setText("▶")

            self._animation = QPropertyAnimation(self._content_widget, b"maximumHeight")
            self._animation.setDuration(100)
            self._animation.setStartValue(self._content_widget.height())
            self._animation.setEndValue(0)
            self._animation.setEasingCurve(QEasingCurve.Type.InQuad)
            self._animation.finished.connect(lambda: self._content_widget.setVisible(False))
            self._animation.start()

    def set_expanded(self, expanded: bool):
        """设置展开状态"""
        if self._expanded != expanded:
            self._toggle_expand()


class ToolCallBubble(DebugBubble):
    """工具调用气泡"""

    def __init__(self, tool_name: str, arguments: dict, parent=None):
        import json
        title = f"调用工具: {tool_name}"
        content = f"```json\n{json.dumps(arguments, indent=2, ensure_ascii=False)}\n```"
        super().__init__("tool_call", title, content, parent)


class RequestBubble(DebugBubble):
    """请求参数气泡"""

    def __init__(self, request_info: str, parent=None):
        title = "请求参数"
        super().__init__("request", title, request_info, parent)


class ResponseBubble(DebugBubble):
    """返回结果气泡"""

    def __init__(self, response_info: str, parent=None):
        title = "返回结果"
        super().__init__("response", title, response_info, parent)


class ThoughtBubble(DebugBubble):
    """思考过程气泡"""

    def __init__(self, thought: str, parent=None):
        title = "思考过程"
        super().__init__("thought", title, thought, parent)
