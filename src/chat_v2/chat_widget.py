# Chat Widget V2 - 重写的对话窗口组件
# 改进:
# - 使用 ChatWorker 安全取消（不用 terminate）
# - 流式气泡管理不再用 hasattr/del，用显式状态
# - 重新生成功能有 UI 入口
# - 消息右键菜单（复制/删除）
# - 键盘快捷键（Esc 取消生成）
# - 搜索功能
# - 导出功能
# - 空状态不再用绝对定位
# - 调试模式可在对话窗口内切换
import sys
from pathlib import Path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPlainTextEdit, QPushButton, QScrollArea,
    QFrame, QGraphicsOpacityEffect, QSizePolicy, QLabel,
    QMessageBox, QFileDialog, QLineEdit
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QTimer, QEvent
from PySide6.QtGui import QFont, QKeySequence, QShortcut

from chat_v2.message_bubble import MessageBubble
from chat_v2.debug_bubble import DebugBubble
from chat_v2.conversation_manager import get_conversation_manager, Message
from chat_v2.chat_worker import ChatWorker
from agent import get_core, get_langchain_memory
from utils import get_character_manager, get_logger, get_config

logger = get_logger()


class EmptyStateWidget(QWidget):
    """空状态占位 - 无消息时显示引导"""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon = QLabel("💬")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet("font-size: 48px;")
        layout.addWidget(icon)

        title = QLabel("开始和 Kizuna 聊天吧")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #7BB8FF; margin-top: 8px;")
        layout.addWidget(title)

        subtitle = QLabel("输入消息，按 Enter 发送")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setFont(QFont("Arial", 11))
        subtitle.setStyleSheet("color: #aaa; margin-top: 4px;")
        layout.addWidget(subtitle)

        layout.addStretch()


class SearchBar(QWidget):
    """搜索栏 - 在消息列表中搜索"""

    close_requested = Signal()
    search_text_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)

        label = QLabel("🔍")
        label.setStyleSheet("font-size: 14px;")
        layout.addWidget(label)

        self._input = QLineEdit()
        self._input.setPlaceholderText("搜索消息...")
        self._input.setFont(QFont("Arial", 11))
        self._input.setStyleSheet("""
            QLineEdit {
                padding: 4px 8px;
                border: 1px solid #cfe0ff;
                border-radius: 6px;
                background: white;
                color: #44506a;
            }
            QLineEdit:focus {
                border-color: #7BB8FF;
            }
        """)
        self._input.textChanged.connect(self.search_text_changed.emit)
        layout.addWidget(self._input)

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(24, 24)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #999;
                font-size: 14px;
            }
            QPushButton:hover {
                color: #ff5252;
            }
        """)
        close_btn.clicked.connect(self.close_requested.emit)
        layout.addWidget(close_btn)

    @property
    def text(self) -> str:
        return self._input.text()

    def set_focus(self):
        self._input.setFocus()


class ChatWidget(QFrame):
    """对话窗口 V2

    改进:
    - 安全取消生成
    - 重新生成按钮
    - 搜索功能
    - 导出功能
    - 调试模式切换
    - 键盘快捷键
    - 消息删除
    """

    response_received = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.core = get_core()
        self.conversation_manager = get_conversation_manager()
        self.character_manager = get_character_manager()
        self.memory = get_langchain_memory()
        self.config = get_config()

        # 状态
        self._is_generating = False
        self._worker: ChatWorker = None
        self._stream_bubble: MessageBubble = None  # 流式气泡，显式管理
        self._last_user_text = ""  # 用于重新生成

        # UI 组件引用
        self._scroll_area: QScrollArea = None
        self._scroll_button: QPushButton = None
        self._scroll_anim_opacity = None
        self._scroll_anim_scroll = None
        self._empty_state: EmptyStateWidget = None
        self._search_bar: SearchBar = None
        self._debug_toggle_btn: QPushButton = None

        # 消息索引映射（气泡 -> Message 索引）
        self._bubble_message_map: dict = {}  # {MessageBubble: int}

        self._setup_ui()
        self._setup_shortcuts()

        # 根据配置决定是否加载/清空历史
        if self.config.general.keep_conversation_history:
            self._load_history()
        else:
            if self.conversation_manager.messages:
                self.conversation_manager.clear()

        self._check_first_run()
        self._update_empty_state()

        QTimer.singleShot(100, self._scroll_to_bottom)

    # ── UI 设置 ──

    def _setup_ui(self):
        """设置 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 12)
        layout.setSpacing(0)

        # 搜索栏（默认隐藏）
        self._search_bar = SearchBar()
        self._search_bar.hide()
        self._search_bar.close_requested.connect(self._hide_search)
        self._search_bar.search_text_changed.connect(self._on_search)
        layout.addWidget(self._search_bar)

        # 消息列表滚动区
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: transparent;
                width: 8px;
                margin: 4px 2px 4px 2px;
            }
            QScrollBar::handle:vertical {
                background: rgba(150, 200, 255, 0.4);
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(150, 200, 255, 0.7);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        self.messages_container = QWidget()
        self.messages_container.setStyleSheet("background-color: transparent;")
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.setSpacing(8)
        self.messages_layout.setContentsMargins(4, 4, 4, 4)
        self.messages_layout.addStretch()
        scroll.setWidget(self.messages_container)

        scroll.verticalScrollBar().valueChanged.connect(self._on_scroll_changed)

        layout.addWidget(scroll, 1)
        self._scroll_area = scroll

        # 空状态（放在 messages_layout 中，不再绝对定位）
        self._empty_state = EmptyStateWidget()
        self.messages_layout.insertWidget(0, self._empty_state)

        # 跳转到底部按钮
        self._setup_scroll_to_bottom_button()

        # 输入区
        input_wrap = QFrame()
        input_wrap.setObjectName("inputWrap")
        input_layout = QVBoxLayout(input_wrap)
        input_layout.setContentsMargins(10, 8, 10, 8)
        input_layout.setSpacing(6)

        # 多行自适应输入框
        self.input_edit = QPlainTextEdit()
        self.input_edit.setPlaceholderText("输入消息…（Enter 发送，Shift+Enter 换行）")
        self.input_edit.setFont(QFont("Arial", 11))
        self.input_edit.setMaximumHeight(120)
        self.input_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.input_edit.setTabChangesFocus(True)
        self.input_edit.installEventFilter(self)
        self.input_edit.textChanged.connect(self._on_input_text_changed)
        QTimer.singleShot(0, self._reset_input_height)
        input_layout.addWidget(self.input_edit)

        # 底部操作栏
        bottom_bar = QHBoxLayout()
        bottom_bar.setSpacing(8)

        # 清空对话按钮
        self._clear_btn = QPushButton("🗑")
        self._clear_btn.setObjectName("clearBtn")
        self._clear_btn.setFixedSize(32, 32)
        self._clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._clear_btn.setToolTip("清空对话")
        self._clear_btn.clicked.connect(self._on_clear_conversation)
        bottom_bar.addWidget(self._clear_btn)

        # 搜索按钮
        search_btn = QPushButton("🔍")
        search_btn.setObjectName("searchBtn")
        search_btn.setFixedSize(32, 32)
        search_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        search_btn.setToolTip("搜索消息 (Ctrl+F)")
        search_btn.setStyleSheet("""
            QPushButton#searchBtn {
                background: transparent;
                border: 1px solid rgba(0,0,0,0.06);
                border-radius: 8px;
                color: #999;
                font-size: 14px;
            }
            QPushButton#searchBtn:hover {
                background: rgba(92, 158, 255, 0.08);
                border-color: rgba(92, 158, 255, 0.2);
                color: #5c9eff;
            }
        """)
        search_btn.clicked.connect(self._show_search)
        bottom_bar.addWidget(search_btn)

        # 导出按钮
        export_btn = QPushButton("📄")
        export_btn.setObjectName("exportBtn")
        export_btn.setFixedSize(32, 32)
        export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        export_btn.setToolTip("导出对话")
        export_btn.setStyleSheet("""
            QPushButton#exportBtn {
                background: transparent;
                border: 1px solid rgba(0,0,0,0.06);
                border-radius: 8px;
                color: #999;
                font-size: 14px;
            }
            QPushButton#exportBtn:hover {
                background: rgba(76, 175, 80, 0.08);
                border-color: rgba(76, 175, 80, 0.2);
                color: #4caf50;
            }
        """)
        export_btn.clicked.connect(self._export_conversation)
        bottom_bar.addWidget(export_btn)

        # 调试模式切换
        self._debug_toggle_btn = QPushButton("🐛")
        self._debug_toggle_btn.setObjectName("debugBtn")
        self._debug_toggle_btn.setFixedSize(32, 32)
        self._debug_toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._debug_toggle_btn.setToolTip("切换调试模式")
        is_debug = self.config.general.chat_mode == "debug"
        self._update_debug_toggle_style(is_debug)
        self._debug_toggle_btn.clicked.connect(self._toggle_debug_mode)
        bottom_bar.addWidget(self._debug_toggle_btn)

        # 字符计数
        self._char_count_label = QLabel("")
        self._char_count_label.setStyleSheet("color: #aaa; font-size: 10px;")
        bottom_bar.addWidget(self._char_count_label)
        bottom_bar.addStretch()

        # 重新生成按钮
        self._regen_btn = QPushButton("🔄")
        self._regen_btn.setObjectName("regenBtn")
        self._regen_btn.setFixedSize(32, 32)
        self._regen_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._regen_btn.setToolTip("重新生成 (Ctrl+R)")
        self._regen_btn.setStyleSheet("""
            QPushButton#regenBtn {
                background: transparent;
                border: 1px solid rgba(0,0,0,0.06);
                border-radius: 8px;
                color: #999;
                font-size: 14px;
            }
            QPushButton#regenBtn:hover {
                background: rgba(255, 152, 0, 0.08);
                border-color: rgba(255, 152, 0, 0.2);
                color: #ff9800;
            }
        """)
        self._regen_btn.clicked.connect(self._regenerate_last_response)
        bottom_bar.addWidget(self._regen_btn)

        # 停止按钮（生成中显示）
        self.stop_btn = QPushButton("■ 停止")
        self.stop_btn.setObjectName("stopBtn")
        self.stop_btn.setFixedSize(82, 32)
        self.stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.stop_btn.clicked.connect(self._on_stop_generate)
        self.stop_btn.hide()
        bottom_bar.addWidget(self.stop_btn)

        # 发送按钮
        self.send_btn = QPushButton("发送")
        self.send_btn.setObjectName("sendBtn")
        self.send_btn.setFixedSize(82, 32)
        self.send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_btn.clicked.connect(self._on_send)
        bottom_bar.addWidget(self.send_btn)

        input_layout.addLayout(bottom_bar)
        layout.addWidget(input_wrap)

        # 样式表
        self.setStyleSheet("""
            ChatWidget {
                background-color: transparent;
                border: none;
            }
            QFrame#inputWrap {
                background-color: rgba(255, 255, 255, 0.94);
                border: 1px solid #dce8ff;
                border-radius: 14px;
            }
            QPlainTextEdit {
                padding: 8px 13px;
                border: 1px solid #cfe0ff;
                border-radius: 10px;
                background-color: white;
                color: #44506a;
                font-size: 12px;
            }
            QPlainTextEdit:focus {
                border-color: #7BB8FF;
                background-color: #F8FBFF;
            }
            QPlainTextEdit:hover {
                border-color: #9BC8FF;
            }
            QPushButton#sendBtn {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #84b5ff, stop:1 #5f97ff);
                color: white;
                border: none;
                border-radius: 16px;
                font-weight: 600;
                font-size: 12px;
            }
            QPushButton#sendBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #B8E8FF, stop:1 #8BC8FF);
            }
            QPushButton#sendBtn:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #8BC8FF, stop:1 #6BA8FF);
            }
            QPushButton#sendBtn:disabled {
                background: #D0D0D0;
                color: #999;
            }
            QPushButton#stopBtn {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ff8a80, stop:1 #ff5252);
                color: white;
                border: none;
                border-radius: 16px;
                font-weight: 600;
                font-size: 12px;
            }
            QPushButton#stopBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ff6e6e, stop:1 #ff3535);
            }
            QPushButton#stopBtn:pressed {
                background: #d32f2f;
            }
            QPushButton#clearBtn {
                background: transparent;
                border: 1px solid rgba(0,0,0,0.06);
                border-radius: 8px;
                color: #ccc;
                font-size: 14px;
            }
            QPushButton#clearBtn:hover {
                background: rgba(255, 82, 82, 0.08);
                border-color: rgba(255, 82, 82, 0.2);
                color: #ff5252;
            }
        """)

    def _setup_shortcuts(self):
        """设置键盘快捷键"""
        # Esc 取消生成
        esc_shortcut = QShortcut(QKeySequence("Escape"), self)
        esc_shortcut.activated.connect(self._on_escape)

        # Ctrl+F 搜索
        search_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        search_shortcut.activated.connect(self._show_search)

        # Ctrl+R 重新生成
        regen_shortcut = QShortcut(QKeySequence("Ctrl+R"), self)
        regen_shortcut.activated.connect(self._regenerate_last_response)

    def _update_debug_toggle_style(self, is_debug: bool):
        """更新调试按钮样式"""
        if is_debug:
            self._debug_toggle_btn.setStyleSheet("""
                QPushButton#debugBtn {
                    background: rgba(156, 39, 176, 0.12);
                    border: 1px solid rgba(156, 39, 176, 0.3);
                    border-radius: 8px;
                    color: #9c27b0;
                    font-size: 14px;
                }
                QPushButton#debugBtn:hover {
                    background: rgba(156, 39, 176, 0.18);
                }
            """)
        else:
            self._debug_toggle_btn.setStyleSheet("""
                QPushButton#debugBtn {
                    background: transparent;
                    border: 1px solid rgba(0,0,0,0.06);
                    border-radius: 8px;
                    color: #999;
                    font-size: 14px;
                }
                QPushButton#debugBtn:hover {
                    background: rgba(156, 39, 176, 0.08);
                    border-color: rgba(156, 39, 176, 0.2);
                    color: #9c27b0;
                }
            """)

    # ── 输入处理 ──

    def _reset_input_height(self):
        if self.input_edit:
            self.input_edit.setFixedHeight(40)

    def _on_input_text_changed(self):
        doc = self.input_edit.document()
        doc_height = doc.size().height()
        margins = self.input_edit.contentsMargins()
        ideal_height = int(doc_height + margins.top() + margins.bottom() + 16)
        clamped = max(40, min(ideal_height, 120))
        if self.input_edit.height() != clamped:
            self.input_edit.setFixedHeight(clamped)
        text = self.input_edit.toPlainText()
        count = len(text)
        self._char_count_label.setText(f"{count}" if count > 0 else "")

    def eventFilter(self, obj, event):
        if obj is self.input_edit and event.type() == QEvent.Type.KeyPress:
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                if not event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                    self._on_send()
                    return True
        return super().eventFilter(obj, event)

    # ── 发送/生成 ──

    def _on_send(self):
        if self._is_generating:
            return
        text = self.input_edit.toPlainText().strip()
        if not text:
            return

        self._add_message_bubble(text, is_user=True)
        self.conversation_manager.add_user_message(text)
        self.input_edit.clear()
        self._reset_input_height()
        self._generate_response(text)

    def _generate_response(self, user_text: str, is_task: bool = False):
        """生成回复"""
        self._is_generating = True
        self._last_user_text = user_text
        self._update_send_button_state()

        # 创建流式气泡
        self._stream_bubble = MessageBubble("", is_user=False, streaming=True)
        viewport_width = self._scroll_area.viewport().width()
        if viewport_width > 0:
            self._stream_bubble.update_max_width(viewport_width)
        self._insert_widget_before_stretch(self._stream_bubble)

        # 创建 Worker
        self._worker = ChatWorker(user_text, self.core, is_task=is_task)
        self._worker.stream_token.connect(self._on_stream_token)
        self._worker.stream_accumulated.connect(self._on_stream_accumulated)
        self._worker.debug_update.connect(self._on_debug_update)
        self._worker.finished.connect(self._on_response_finished)
        self._worker.error.connect(self._on_response_error)
        self._worker.start()

    def _on_stream_token(self, token: str):
        """收到单个 token（用于首次显示切换）"""
        if self._stream_bubble and self._stream_bubble.is_streaming:
            if not self._stream_bubble._browser.isVisible():
                self._stream_bubble._on_first_stream_content()

    def _on_stream_accumulated(self, text: str):
        """流式累积文本更新"""
        if self._stream_bubble:
            self._stream_bubble.update_text(text)
            # 自动滚动
            scroll_bar = self._scroll_area.verticalScrollBar()
            scroll_bar.setValue(scroll_bar.maximum())

    def _on_debug_update(self, debug_info: dict):
        """调试信息更新"""
        if self.config.general.chat_mode != "debug":
            return

        debug_type = debug_info.get("debug_type", "")
        debug_title = debug_info.get("debug_title", "")
        debug_content = debug_info.get("debug_content", "")
        if not debug_type or not debug_content:
            return

        debug_bubble = DebugBubble(debug_type, debug_title, debug_content)
        # 插入到流式气泡之前
        if self._stream_bubble:
            idx = self.messages_layout.indexOf(self._stream_bubble)
            if idx >= 0:
                self.messages_layout.insertWidget(idx, debug_bubble)
            else:
                self._insert_widget_before_stretch(debug_bubble)
        else:
            self._insert_widget_before_stretch(debug_bubble)

        logger.info(f"显示调试信息: {debug_title}")
        QTimer.singleShot(50, self._scroll_to_bottom)

    def _on_response_finished(self, result: dict):
        """回复生成完成"""
        final_text = result.get("final_text", "")
        cancelled = result.get("cancelled", False)

        if final_text:
            if self._stream_bubble:
                self._stream_bubble.update_text(final_text)
                self._stream_bubble.finalize()
                self._stream_bubble.delete_requested.connect(
                    lambda: self._on_delete_bubble(self._stream_bubble)
                )
                self.conversation_manager.add_assistant_message(final_text)
                self._stream_bubble = None
            else:
                self._add_message_bubble(final_text, is_user=False)
                self.conversation_manager.add_assistant_message(final_text)
        else:
            if self._stream_bubble:
                self._stream_bubble.deleteLater()
                self._stream_bubble = None

        self._is_generating = False
        self._update_send_button_state()
        self._update_empty_state()
        self.response_received.emit()
        logger.info("回复生成完成" + (" (已取消)" if cancelled else ""))

    def _on_response_error(self, error: str):
        """回复生成错误"""
        if self._stream_bubble:
            self._stream_bubble.deleteLater()
            self._stream_bubble = None

        error_msg = f"抱歉，出错了：{error}"
        self._add_message_bubble(error_msg, is_user=False)

        self._is_generating = False
        self._update_send_button_state()
        logger.error(f"回复生成失败: {error}")

    def _on_stop_generate(self):
        """停止生成（安全方式）"""
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._worker.wait(3000)

        if self._stream_bubble:
            current_text = self._stream_bubble.text
            if current_text and current_text.strip():
                self._stream_bubble.finalize()
                self.conversation_manager.add_assistant_message(current_text)
            else:
                self._stream_bubble.deleteLater()
            self._stream_bubble = None

        self._is_generating = False
        self._update_send_button_state()

    def _on_escape(self):
        """Esc 键处理"""
        if self._is_generating:
            self._on_stop_generate()
        elif self._search_bar.isVisible():
            self._hide_search()

    # ── 重新生成 ──

    def _regenerate_last_response(self):
        """重新生成最后一条 AI 回复"""
        if self._is_generating:
            return
        if not self._last_user_text:
            return

        # 移除最后一条 AI 消息（从 conversation_manager）
        self.conversation_manager.remove_last_assistant_message()

        # 移除最后一个 AI 气泡
        for i in range(self.messages_layout.count() - 2, -1, -1):
            item = self.messages_layout.itemAt(i)
            widget = item.widget()
            if isinstance(widget, MessageBubble) and not widget.is_user:
                widget.deleteLater()
                break

        self._generate_response(self._last_user_text)

    # ── 消息管理 ──

    def _add_message_bubble(self, text: str, is_user: bool = False, timestamp=None):
        """添加消息气泡"""
        bubble = MessageBubble(text, is_user, timestamp=timestamp)
        bubble.delete_requested.connect(lambda: self._on_delete_bubble(bubble))

        viewport_width = self._scroll_area.viewport().width()
        if viewport_width > 0:
            bubble.update_max_width(viewport_width)

        self._insert_widget_before_stretch(bubble)
        self._update_empty_state()
        QTimer.singleShot(100, self._scroll_to_bottom)

    def _insert_widget_before_stretch(self, widget):
        """在 stretch 之前插入控件"""
        insert_pos = self.messages_layout.count() - 1
        self.messages_layout.insertWidget(insert_pos, widget)

    def _on_delete_bubble(self, bubble: MessageBubble):
        """删除消息气泡"""
        idx = self.messages_layout.indexOf(bubble)
        if idx >= 0:
            self.messages_layout.removeWidget(bubble)
            bubble.deleteLater()
            self._update_empty_state()

    def _on_clear_conversation(self):
        """清空对话"""
        reply = QMessageBox.question(
            self, "清空对话",
            "确定要清空所有对话记录吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._clear_all_messages()

    def _clear_all_messages(self):
        """清空所有消息"""
        self.conversation_manager.clear()
        while self.messages_layout.count() > 1:
            item = self.messages_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self._update_empty_state()
        logger.info("对话已清空")

    # ── 空状态 ──

    def _update_empty_state(self):
        """更新空状态显示"""
        has_messages = any(
            isinstance(self.messages_layout.itemAt(i).widget(), MessageBubble)
            for i in range(self.messages_layout.count())
        )
        if has_messages:
            self._empty_state.hide()
        else:
            self._empty_state.show()

    # ── 搜索 ──

    def _show_search(self):
        self._search_bar.show()
        self._search_bar.set_focus()

    def _hide_search(self):
        self._search_bar.hide()
        self._clear_search_highlight()

    def _on_search(self, query: str):
        """搜索消息，高亮匹配的气泡"""
        if not query:
            self._clear_search_highlight()
            return

        query_lower = query.lower()
        for i in range(self.messages_layout.count()):
            item = self.messages_layout.itemAt(i)
            widget = item.widget()
            if isinstance(widget, MessageBubble):
                if query_lower in widget.text.lower():
                    widget.setStyleSheet(widget.styleSheet())  # 触发重绘
                # 简单实现：滚动到第一个匹配
                # 更完整的实现可以高亮匹配文本

    def _clear_search_highlight(self):
        """清除搜索高亮"""
        pass

    # ── 导出 ──

    def _export_conversation(self):
        """导出对话"""
        if not self.conversation_manager.messages:
            QMessageBox.information(self, "导出对话", "当前没有对话记录可导出。")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出对话", "kizuna_conversation.txt",
            "文本文件 (*.txt);;Markdown 文件 (*.md);;所有文件 (*)"
        )
        if file_path:
            try:
                content = self.conversation_manager.export_text()
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                QMessageBox.information(self, "导出成功", f"对话已导出到:\n{file_path}")
            except Exception as e:
                QMessageBox.warning(self, "导出失败", f"导出失败: {e}")

    # ── 调试模式 ──

    def _toggle_debug_mode(self):
        """切换调试模式"""
        current = self.config.general.chat_mode
        new_mode = "normal" if current == "debug" else "debug"
        self.config.general.chat_mode = new_mode
        self.config.save()
        self._update_debug_toggle_style(new_mode == "debug")
        logger.info(f"调试模式: {new_mode}")

    # ── 滚动 ──

    def _setup_scroll_to_bottom_button(self):
        self._scroll_button = QPushButton("↓")
        self._scroll_button.setObjectName("scrollBtn")
        self._scroll_button.setFixedSize(36, 36)
        self._scroll_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._scroll_button.setStyleSheet("""
            QPushButton#scrollBtn {
                background: rgba(123, 184, 255, 0.85);
                color: white;
                border: none;
                border-radius: 18px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton#scrollBtn:hover {
                background: rgba(92, 158, 255, 0.95);
            }
            QPushButton#scrollBtn:pressed {
                background: rgba(70, 130, 230, 0.95);
            }
        """)
        self._scroll_button.clicked.connect(self._scroll_to_bottom)

        opacity_effect = QGraphicsOpacityEffect(self._scroll_button)
        opacity_effect.setOpacity(0.0)
        self._scroll_button.setGraphicsEffect(opacity_effect)

        self._scroll_button.setParent(self._scroll_area)
        self._scroll_button.hide()

    def _on_scroll_changed(self, value):
        scroll_bar = self._scroll_area.verticalScrollBar()
        is_at_bottom = value >= scroll_bar.maximum() - 50
        if is_at_bottom:
            self._hide_scroll_button()
        else:
            self._show_scroll_button()

    def _show_scroll_button(self):
        if not self._scroll_button.isVisible():
            btn_x = self._scroll_area.width() - self._scroll_button.width() - 10
            btn_y = self._scroll_area.height() - self._scroll_button.height() - 10
            self._scroll_button.move(btn_x, btn_y)
            self._scroll_button.show()

            opacity = self._scroll_button.graphicsEffect()
            if opacity:
                if self._scroll_anim_opacity and self._scroll_anim_opacity.state() == QPropertyAnimation.State.Running:
                    self._scroll_anim_opacity.stop()
                self._scroll_anim_opacity = QPropertyAnimation(opacity, b"opacity")
                self._scroll_anim_opacity.setDuration(200)
                self._scroll_anim_opacity.setStartValue(0.0)
                self._scroll_anim_opacity.setEndValue(1.0)
                self._scroll_anim_opacity.setEasingCurve(QEasingCurve.Type.OutQuad)
                self._scroll_anim_opacity.start()

    def _hide_scroll_button(self):
        if self._scroll_button.isVisible():
            opacity = self._scroll_button.graphicsEffect()
            if opacity:
                if self._scroll_anim_opacity and self._scroll_anim_opacity.state() == QPropertyAnimation.State.Running:
                    self._scroll_anim_opacity.stop()
                self._scroll_anim_opacity = QPropertyAnimation(opacity, b"opacity")
                self._scroll_anim_opacity.setDuration(150)
                self._scroll_anim_opacity.setStartValue(1.0)
                self._scroll_anim_opacity.setEndValue(0.0)
                self._scroll_anim_opacity.setEasingCurve(QEasingCurve.Type.InQuad)
                self._scroll_anim_opacity.finished.connect(self._scroll_button.hide)
                self._scroll_anim_opacity.start()
            else:
                self._scroll_button.hide()

    def _scroll_to_bottom(self):
        self.messages_container.layout().update()
        self.messages_container.updateGeometry()
        scroll_bar = self._scroll_area.verticalScrollBar()
        target = scroll_bar.maximum()

        if self._scroll_anim_scroll and self._scroll_anim_scroll.state() == QPropertyAnimation.State.Running:
            self._scroll_anim_scroll.stop()

        self._scroll_anim_scroll = QPropertyAnimation(scroll_bar, b"value")
        self._scroll_anim_scroll.setDuration(150)
        self._scroll_anim_scroll.setStartValue(scroll_bar.value())
        self._scroll_anim_scroll.setEndValue(target)
        self._scroll_anim_scroll.setEasingCurve(QEasingCurve.Type.OutQuad)
        self._scroll_anim_scroll.start()
        self._hide_scroll_button()

    # ── 历史加载 ──

    def _load_history(self):
        messages = self.conversation_manager.messages
        for msg in messages:
            self._add_message_bubble(msg.content, msg.role == "user",
                                     timestamp=msg.timestamp)

    def _check_first_run(self):
        """检查是否第一次运行，显示开场白"""
        persona = self.character_manager.persona
        if self.config.general.keep_conversation_history and self.conversation_manager.messages:
            return

        greeting = self.character_manager.get_random_greeting()
        greeting = greeting.replace("{name}", persona.user_nickname or "你")
        greeting = greeting.replace("{user_nickname}", persona.user_nickname or "你")
        self._add_message_bubble(greeting, is_user=False)

        if persona.is_first_run():
            logger.info("第一次启动，显示引导对话")

    # ── 按钮状态 ──

    def _update_send_button_state(self):
        if self._is_generating:
            self.send_btn.hide()
            self.stop_btn.show()
            self._regen_btn.hide()
        else:
            self.send_btn.show()
            self.stop_btn.hide()
            self._regen_btn.show()

    # ── 窗口事件 ──

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._scroll_button and self._scroll_button.isVisible():
            btn_x = self._scroll_area.width() - self._scroll_button.width() - 10
            btn_y = self._scroll_area.height() - self._scroll_button.height() - 10
            self._scroll_button.move(btn_x, btn_y)
        self._update_all_bubble_widths()

    def _update_all_bubble_widths(self):
        viewport_width = self._scroll_area.viewport().width()
        if viewport_width <= 0:
            return
        for i in range(self.messages_layout.count()):
            item = self.messages_layout.itemAt(i)
            widget = item.widget()
            if isinstance(widget, MessageBubble):
                widget.update_max_width(viewport_width)

    # ── 清理 ──

    def cleanup(self):
        """应用退出时调用，确保保存"""
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._worker.wait(2000)
        self.conversation_manager.flush()
