# Debug Bubble Widget - 可折叠的调试信息气泡
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QColor


class DebugBubble(QWidget):
    """可折叠的调试信息气泡"""
    
    def __init__(self, debug_type: str, title: str, content: str, parent=None):
        """
        Args:
            debug_type: 调试类型 (tool_call, request, response, thought)
            title: 标题
            content: 内容
        """
        super().__init__(parent)
        self._debug_type = debug_type
        self._title = title
        self._content = content
        self._expanded = False
        self._content_widget = None
        self._content_label = None
        self._animation = None
        self._setup_ui()
    
    def _setup_ui(self):
        """设置 UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 4, 8, 4)
        main_layout.setSpacing(0)
        
        # 标题栏（可点击折叠）
        header = QWidget()
        header.setCursor(Qt.CursorShape.PointingHandCursor)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 8, 12, 8)
        header_layout.setSpacing(8)
        
        # 展开/折叠图标
        self._toggle_btn = QLabel("▶")
        self._toggle_btn.setFixedWidth(15)
        self._toggle_btn.setStyleSheet("color: #666; font-size: 10px;")
        header_layout.addWidget(self._toggle_btn)
        
        # 图标和标题
        icon = self._get_icon()
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 14px;")
        header_layout.addWidget(icon_label)
        
        title_label = QLabel(self._title)
        title_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: {self._get_title_color()};")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # 设置标题栏样式
        header.setStyleSheet(f"""
            QWidget {{
                background-color: {self._get_header_bg()};
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                border-bottom-left-radius: {0 if self._expanded else 8}px;
                border-bottom-right-radius: {0 if self._expanded else 8}px;
            }}
            QWidget:hover {{
                background-color: {self._get_header_bg(hover=True)};
            }}
        """)
        
        main_layout.addWidget(header)
        
        # 内容区域（默认折叠）
        self._content_widget = QFrame()
        self._content_widget.setStyleSheet(f"""
            QFrame {{
                background-color: {self._get_content_bg()};
                border-bottom-left-radius: 8px;
                border-bottom-right-radius: 8px;
            }}
        """)
        
        content_layout = QVBoxLayout(self._content_widget)
        content_layout.setContentsMargins(12, 8, 12, 8)
        
        self._content_label = QLabel(self._content)
        self._content_label.setWordWrap(True)
        self._content_label.setTextFormat(Qt.TextFormat.MarkdownText)
        self._content_label.setFont(QFont("Consolas", 9))
        self._content_label.setStyleSheet("color: #555; background: transparent;")
        content_layout.addWidget(self._content_label)
        
        # 初始折叠状态
        self._content_widget.setMaximumHeight(0)
        self._content_widget.setVisible(False)
        main_layout.addWidget(self._content_widget)
        
        # 点击标题栏切换折叠
        header.mousePressEvent = lambda e: self._toggle_expand()
        
        # 添加阴影
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(6)
        shadow.setColor(QColor(0, 0, 0, 20))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)
    
    def _get_icon(self) -> str:
        """获取图标"""
        icons = {
            "tool_call": "🔧",
            "request": "📤",
            "response": "📥",
            "thought": "💭",
        }
        return icons.get(self._debug_type, "📋")
    
    def _get_title_color(self) -> str:
        """获取标题颜色"""
        colors = {
            "tool_call": "#5c9eff",
            "request": "#ff9800",
            "response": "#4caf50",
            "thought": "#9c27b0",
        }
        return colors.get(self._debug_type, "#666")
    
    def _get_header_bg(self, hover: bool = False) -> str:
        """获取标题栏背景色"""
        colors = {
            "tool_call": "#e3f2fd" if not hover else "#bbdefb",
            "request": "#fff3e0" if not hover else "#ffe0b2",
            "response": "#e8f5e9" if not hover else "#c8e6c9",
            "thought": "#f3e5f5" if not hover else "#e1bee7",
        }
        return colors.get(self._debug_type, "#f5f5f5")
    
    def _get_content_bg(self) -> str:
        """获取内容区背景色"""
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
            # 展开
            self._toggle_btn.setText("▼")
            self._content_widget.setVisible(True)
            
            # 动画展开
            self._animation = QPropertyAnimation(self._content_widget, b"maximumHeight")
            self._animation.setDuration(150)
            self._animation.setStartValue(0)
            self._animation.setEndValue(self._content_label.sizeHint().height() + 20)
            self._animation.setEasingCurve(QEasingCurve.Type.OutQuad)
            self._animation.start()
        else:
            # 折叠
            self._toggle_btn.setText("▶")
            
            # 动画折叠
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
