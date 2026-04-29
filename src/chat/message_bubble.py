# Message Bubble Widget - Markdown 渲染 + 头像 + 时间戳 + 打字指示器
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextBrowser,
    QGraphicsDropShadowEffect, QLabel, QSizePolicy
)
from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QFont, QColor, QPixmap, QPainter, QTextDocument

from chat.markdown_renderer import render_markdown, MESSAGE_CSS, USER_MESSAGE_CSS


def _create_circle_pixmap(color: QColor, size: int = 36, text: str = "") -> QPixmap:
    """生成圆形纯色头像，中间显示文字首字母"""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    # 画圆
    painter.setBrush(color)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(0, 0, size, size)
    # 画文字
    if text:
        font = QFont("Arial", 14, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(0, 0, size, size,
                         Qt.AlignmentFlag.AlignCenter, text[0].upper())
    painter.end()
    return pixmap


class TypingIndicator(QWidget):
    """打字指示器 — 三个跳动圆点"""

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
    """消息气泡 — 头像 + 时间戳 + Markdown 渲染"""

    def __init__(self, text: str, is_user: bool = False, streaming: bool = False,
                 timestamp: datetime = None, parent=None):
        super().__init__(parent)
        self._text = text
        self._is_user = is_user
        self._streaming = streaming
        self._timestamp = timestamp or datetime.now()
        self._browser = None
        self._typing_indicator = None
        self._bubble_wrapper = None
        self._adjusting = False
        self._width_adjusting = False  # 防止宽度调整递归
        self._last_bubble_width = -1   # 上次设置的气泡宽度，-1 表示未设置
        self._max_bubble_width = 600   # 默认最大气泡宽度，由 update_max_width 更新
        self._setup_ui()

    def update_text(self, text: str):
        """更新文本（流式输出用）"""
        self._text = text
        if self._browser:
            if self._streaming:
                self._browser.setPlainText(text)
            else:
                self._set_html(text)

    def finalize(self):
        """结束流式模式，渲染完整 Markdown"""
        if self._streaming:
            self._streaming = False
            # 移除打字指示器
            if self._typing_indicator:
                self._typing_indicator.stop()
                self._typing_indicator.deleteLater()
                self._typing_indicator = None
            self._set_html(self._text)
            self._browser.show()
            self._adjust_browser_height()
            self._adjust_bubble_width()

    def _set_html(self, text: str):
        """设置 HTML 内容"""
        if self._is_user:
            html = render_markdown(text)
            css = USER_MESSAGE_CSS
        else:
            html = render_markdown(text)
            css = MESSAGE_CSS
        self._browser.setHtml(
            f"<html><head><style>{css}</style></head><body>{html}</body></html>"
        )

    def _format_time(self) -> str:
        """格式化时间戳 — 显示年月日时分"""
        return self._timestamp.strftime("%Y-%m-%d %H:%M")

    def _adjust_browser_height(self):
        """根据文档内容自动调整浏览器高度"""
        if self._adjusting or not self._browser or not self._browser.isVisible():
            return
        # 宽度调整期间不处理，防止递归
        if self._width_adjusting:
            return
        self._adjusting = True
        try:
            doc_height = self._browser.document().size().height()
            if doc_height <= 0:
                return
            margins = self._browser.contentsMargins()
            total_height = int(doc_height + margins.top() + margins.bottom() + 4)
            new_height = max(total_height, 20)
            if self._browser.height() != new_height:
                self._browser.setFixedHeight(new_height)

            # 非流式模式下延迟调整气泡宽度（等布局完成后）
            if not self._streaming:
                QTimer.singleShot(0, self._adjust_bubble_width)
        finally:
            self._adjusting = False

    def _adjust_bubble_width(self):
        """根据内容调整气泡宽度：最小为文字宽度，最大为窗口的 80%"""
        if not self._browser or not self._browser.isVisible() or self._streaming:
            return
        # 防止递归
        if self._width_adjusting:
            return

        self._width_adjusting = True
        try:
            doc = self._browser.document()

            # 先确保气泡以最大宽度渲染，让文档正确布局
            self._bubble_wrapper.setMinimumWidth(0)
            self._bubble_wrapper.setMaximumWidth(self._max_bubble_width)

            # 使用文档的 idealWidth 获取内容实际需要的最大行宽
            try:
                ideal_width = int(doc.idealWidth())
            except AttributeError:
                ideal_width = int(doc.size().width())

            # padding: browser padding(2*2) + bubble margins(10*2) + 额外余量
            padding = 36
            needed_width = ideal_width + padding

            if needed_width >= self._max_bubble_width:
                target_width = self._max_bubble_width
            else:
                target_width = needed_width

            # 宽度未变则跳过，避免触发无意义的重排
            if self._last_bubble_width == target_width:
                return

            self._last_bubble_width = target_width

            if needed_width >= self._max_bubble_width:
                # 内容需要换行，使用最大宽度
                self._bubble_wrapper.setMinimumWidth(0)
                self._bubble_wrapper.setMaximumWidth(self._max_bubble_width)
            else:
                # 内容较短，收缩到理想宽度
                self._bubble_wrapper.setMinimumWidth(target_width)
                self._bubble_wrapper.setMaximumWidth(target_width)
        finally:
            self._width_adjusting = False

    def _setup_ui(self):
        """设置 UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)

        # ── 头像 ──
        avatar_label = QLabel()
        avatar_label.setFixedSize(36, 36)
        if self._is_user:
            pixmap = _create_circle_pixmap(QColor(0x7B, 0xB8, 0xFF), 36, "U")
        else:
            pixmap = _create_circle_pixmap(QColor(0xFF, 0xB7, 0xC5), 36, "K")
        avatar_label.setPixmap(pixmap)
        avatar_label.setAlignment(Qt.AlignmentFlag.AlignTop)

        # ── 气泡容器 ──
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

        # 文本浏览器 — 不限制高度，展示所有内容
        self._browser = QTextBrowser()
        self._browser.setOpenExternalLinks(True)
        self._browser.setReadOnly(True)
        self._browser.setFont(QFont("Arial", 11))
        self._browser.setFrameShape(QTextBrowser.Shape.NoFrame)
        self._browser.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._browser.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._browser.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)

        # 流式模式：显示打字指示器，隐藏浏览器
        if self._streaming:
            self._browser.hide()
            self._typing_indicator = TypingIndicator()
            bubble_layout.addWidget(self._typing_indicator)
        else:
            self._set_html(self._text)

        # 文档内容变化时自动调整高度
        self._browser.document().documentLayout().documentSizeChanged.connect(
            self._adjust_browser_height
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

        # 时间戳 — 无背景，简洁样式
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

        # ── 整体布局 ──
        # MessageBubble 占满宽度，内部用 stretch 推气泡到一侧
        if self._is_user:
            layout.addStretch(1)
            layout.addWidget(self._bubble_wrapper)
            layout.addWidget(avatar_label)
        else:
            layout.addWidget(avatar_label)
            layout.addWidget(self._bubble_wrapper)
            layout.addStretch(1)

        # MessageBubble 自身占满可用宽度，高度随内容
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)

    def update_max_width(self, container_width: int):
        """根据容器宽度更新气泡最大宽度 — 由 ChatWidget 调用"""
        max_width = int(container_width * 0.80)
        clamped = max(min(max_width, 800), 150)
        self._max_bubble_width = clamped
        # 最大宽度变了，需要重新计算
        self._last_bubble_width = -1
        if self._bubble_wrapper:
            self._bubble_wrapper.setMaximumWidth(clamped)
        # 重新计算气泡宽度
        self._adjust_bubble_width()
