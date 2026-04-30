# Message Bubble V2 - 改进的消息气泡组件
# 改进:
# - 移除递归布局问题，使用更简洁的高度/宽度调整
# - 支持右键菜单（复制、删除）
# - 流式更新不再直接访问私有成员
# - 更好的打字指示器生命周期管理
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextBrowser,
    QGraphicsDropShadowEffect, QLabel, QSizePolicy, QMenu
)
from PySide6.QtCore import Qt, QSize, QTimer, Signal
from PySide6.QtGui import QFont, QColor, QPixmap, QPainter, QAction

from chat_v2.markdown_renderer import render_markdown, MESSAGE_CSS, USER_MESSAGE_CSS


def _create_circle_pixmap(color: QColor, size: int = 36, text: str = "") -> QPixmap:
    """生成圆形纯色头像"""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(color)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(0, 0, size, size)
    if text:
        font = QFont("Arial", 14, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(0, 0, size, size,
                         Qt.AlignmentFlag.AlignCenter, text[0].upper())
    painter.end()
    return pixmap


class TypingIndicator(QWidget):
    """打字指示器 - 三个跳动圆点"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(28)
        self._dots = []
        self._step = 0
        self._timer = QTimer(self)
        self._timer.setInterval(300)
        self._timer.timeout.connect(self._animate)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 4, 12, 4)
        layout.setSpacing(4)

        for _ in range(3):
            dot = QLabel("●")
            dot.setFixedSize(10, 10)
            dot.setAlignment(Qt.AlignmentFlag.AlignCenter)
            dot.setStyleSheet("color: #7BB8FF; font-size: 10px;")
            layout.addWidget(dot)
            self._dots.append(dot)

        layout.addStretch()
        self._timer.start()

    def _animate(self):
        self._step = (self._step + 1) % 3
        for i, dot in enumerate(self._dots):
            if i == self._step:
                dot.setStyleSheet("color: #5c9eff; font-size: 12px; font-weight: bold;")
            else:
                dot.setStyleSheet("color: #cfe0ff; font-size: 8px;")

    def stop(self):
        self._timer.stop()


class MessageBubble(QWidget):
    """消息气泡 V2

    改进:
    - 右键菜单支持复制/删除
    - 流式更新通过公开方法，不暴露内部成员
    - 宽度调整不再递归，使用 QTimer.singleShot 延迟
    - 信号通知外部删除请求
    """

    delete_requested = Signal()  # 请求删除此消息

    def __init__(self, text: str, is_user: bool = False, streaming: bool = False,
                 timestamp: datetime = None, parent=None):
        super().__init__(parent)
        self._text = text
        self._is_user = is_user
        self._streaming = streaming
        self._timestamp = timestamp or datetime.now()
        self._browser: QTextBrowser = None
        self._typing_indicator: TypingIndicator = None
        self._bubble_wrapper: QWidget = None
        self._max_bubble_width = 600
        self._adjust_pending = False  # 防抖标志，避免 documentSizeChanged 循环
        self._setup_ui()
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    # ── 公开接口 ──

    def update_text(self, text: str):
        """更新文本（流式输出用）"""
        self._text = text
        if self._browser:
            if self._streaming:
                # 流式模式用纯文本，避免频繁 Markdown 解析
                self._browser.setPlainText(text)
            else:
                self._set_html(text)

    def finalize(self):
        """结束流式模式，渲染完整 Markdown"""
        if not self._streaming:
            return
        self._streaming = False
        if self._typing_indicator:
            self._typing_indicator.stop()
            self._typing_indicator.deleteLater()
            self._typing_indicator = None
        self._browser.show()
        self._set_html(self._text)
        QTimer.singleShot(0, self._adjust_size)

    def update_max_width(self, container_width: int):
        """根据容器宽度更新气泡最大宽度"""
        max_width = int(container_width * 0.80)
        clamped = max(min(max_width, 800), 150)
        self._max_bubble_width = clamped
        if self._bubble_wrapper:
            self._bubble_wrapper.setMaximumWidth(clamped)
        if not self._streaming:
            QTimer.singleShot(0, self._adjust_size)

    @property
    def is_user(self) -> bool:
        return self._is_user

    @property
    def text(self) -> str:
        return self._text

    @property
    def is_streaming(self) -> bool:
        return self._streaming

    # ── 右键菜单 ──

    def _show_context_menu(self, pos):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background: #e3f2fd;
                color: #1565c0;
            }
        """)

        copy_action = QAction("复制文本", self)
        copy_action.triggered.connect(self._copy_text)
        menu.addAction(copy_action)

        delete_action = QAction("删除消息", self)
        delete_action.triggered.connect(self.delete_requested.emit)
        menu.addAction(delete_action)

        menu.exec(self.mapToGlobal(pos))

    def _copy_text(self):
        """复制消息文本到剪贴板"""
        from PySide6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(self._text)

    # ── 内部方法 ──

    def _set_html(self, text: str):
        """设置 HTML 内容"""
        html = render_markdown(text)
        css = USER_MESSAGE_CSS if self._is_user else MESSAGE_CSS
        self._browser.setHtml(
            f"<html><head><style>{css}</style></head><body>{html}</body></html>"
        )

    def _format_time(self) -> str:
        return self._timestamp.strftime("%Y-%m-%d %H:%M")

    def _adjust_size(self):
        """统一调整浏览器高度和气泡宽度（带防抖，避免 documentSizeChanged 循环）"""
        if not self._browser or not self._browser.isVisible():
            return
        if self._adjust_pending:
            return
        self._adjust_pending = True
        try:
            self._do_adjust_size()
        finally:
            # 延迟重置防抖标志，防止同一次事件循环内重复调整
            QTimer.singleShot(0, self._reset_adjust_pending)

    def _reset_adjust_pending(self):
        self._adjust_pending = False

    def _do_adjust_size(self):
        """实际执行尺寸调整"""
        # 调整浏览器高度
        doc = self._browser.document()
        doc_height = doc.size().height()
        if doc_height > 0:
            margins = self._browser.contentsMargins()
            total = int(doc_height + margins.top() + margins.bottom() + 4)
            new_h = max(total, 20)
            if self._browser.height() != new_h:
                self._browser.setFixedHeight(new_h)

        # 调整气泡宽度
        if self._streaming or not self._bubble_wrapper:
            return
        try:
            ideal_width = int(doc.idealWidth())
        except AttributeError:
            ideal_width = int(doc.size().width())
        padding = 36
        needed = ideal_width + padding
        target = min(needed, self._max_bubble_width)
        if needed >= self._max_bubble_width:
            self._bubble_wrapper.setMinimumWidth(0)
        else:
            self._bubble_wrapper.setMinimumWidth(target)
        self._bubble_wrapper.setMaximumWidth(self._max_bubble_width)

    def _on_first_stream_content(self):
        """首次收到流式内容时切换显示"""
        if self._typing_indicator:
            self._typing_indicator.stop()
            self._typing_indicator.hide()
        self._browser.show()

    def _setup_ui(self):
        """设置 UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)

        # 头像
        avatar_label = QLabel()
        avatar_label.setFixedSize(36, 36)
        if self._is_user:
            pixmap = _create_circle_pixmap(QColor(0x7B, 0xB8, 0xFF), 36, "U")
        else:
            pixmap = _create_circle_pixmap(QColor(0xFF, 0xB7, 0xC5), 36, "K")
        avatar_label.setPixmap(pixmap)
        avatar_label.setAlignment(Qt.AlignmentFlag.AlignTop)

        # 气泡容器
        self._bubble_wrapper = QWidget()
        self._bubble_wrapper.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        self._bubble_wrapper.setMaximumWidth(600)
        wrapper_layout = QVBoxLayout(self._bubble_wrapper)
        wrapper_layout.setContentsMargins(0, 0, 0, 0)
        wrapper_layout.setSpacing(0)

        # 气泡主体
        bubble = QWidget()
        bubble_layout = QVBoxLayout(bubble)
        bubble_layout.setContentsMargins(10, 8, 10, 8)
        bubble_layout.setSpacing(2)

        # 文本浏览器
        self._browser = QTextBrowser()
        self._browser.setOpenExternalLinks(True)
        self._browser.setReadOnly(True)
        self._browser.setFont(QFont("Arial", 11))
        self._browser.setFrameShape(QTextBrowser.Shape.NoFrame)
        self._browser.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._browser.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._browser.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)

        # 流式模式
        if self._streaming:
            self._browser.hide()
            self._typing_indicator = TypingIndicator()
            bubble_layout.addWidget(self._typing_indicator)
        else:
            self._set_html(self._text)

        # 文档变化时自动调整（通过防抖的 _adjust_size 避免循环）
        self._browser.document().documentLayout().documentSizeChanged.connect(
            self._adjust_size
        )

        # 浏览器样式
        if self._is_user:
            self._browser.setStyleSheet("""
                QTextBrowser {
                    background: transparent;
                    color: white;
                    border: none;
                    padding: 2px;
                }
            """)
        else:
            self._browser.setStyleSheet("""
                QTextBrowser {
                    background: transparent;
                    color: #444;
                    border: none;
                    padding: 2px;
                    selection-background-color: #a8d8ff;
                    selection-color: #333;
                }
            """)

        bubble_layout.addWidget(self._browser)

        # 时间戳
        time_label = QLabel(self._format_time())
        time_label.setFont(QFont("Arial", 9))
        if self._is_user:
            time_label.setStyleSheet(
                "color: rgba(255,255,255,0.55); margin-top: 2px; background: none;")
            time_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        else:
            time_label.setStyleSheet(
                "color: #ccc; margin-top: 2px; background: none;")
            time_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        bubble_layout.addWidget(time_label)

        # 气泡样式
        if self._is_user:
            bubble.setStyleSheet("""
                QWidget {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #A8D8FF, stop:1 #7BB8FF);
                    border-radius: 16px;
                    border-top-right-radius: 4px;
                }
            """)
        else:
            bubble.setStyleSheet("""
                QWidget {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #FFFFFF, stop:1 #FFF5F8);
                    border: 1px solid #FFE8F0;
                    border-radius: 16px;
                    border-top-left-radius: 4px;
                }
            """)

        # 阴影
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(8)
        shadow.setColor(QColor(0, 0, 0, 25))
        shadow.setOffset(0, 2)
        bubble.setGraphicsEffect(shadow)

        wrapper_layout.addWidget(bubble)

        # 整体布局
        if self._is_user:
            layout.addStretch(1)
            layout.addWidget(self._bubble_wrapper)
            layout.addWidget(avatar_label)
        else:
            layout.addWidget(avatar_label)
            layout.addWidget(self._bubble_wrapper)
            layout.addStretch(1)

        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
