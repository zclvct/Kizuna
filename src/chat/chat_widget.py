# Chat Widget
import sys
import asyncio
from pathlib import Path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPlainTextEdit, QPushButton, QScrollArea,
    QFrame, QGraphicsOpacityEffect, QSizePolicy, QLabel,
    QMessageBox
)
from PySide6.QtCore import Qt, Signal, QThread, QPropertyAnimation, QEasingCurve, QTimer, QEvent
from PySide6.QtGui import QFont

from chat.message_bubble import MessageBubble
from chat.debug_bubble import DebugBubble
from chat.conversation_manager import get_conversation_manager
from agent import get_core, get_langchain_memory
from utils import get_character_manager, get_logger, get_config

logger = get_logger()


class EmptyStateWidget(QWidget):
    """空状态占位 — 无消息时显示引导"""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 图标
        icon = QLabel("💬")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet("font-size: 48px;")
        layout.addWidget(icon)

        # 标题
        title = QLabel("开始和 Kizuna 聊天吧")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #7BB8FF; margin-top: 8px;")
        layout.addWidget(title)

        # 副标题
        subtitle = QLabel("输入消息，按 Enter 发送")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setFont(QFont("Arial", 11))
        subtitle.setStyleSheet("color: #aaa; margin-top: 4px;")
        layout.addWidget(subtitle)

        layout.addStretch()


class ChatWidget(QFrame):
    """对话窗口 - 二次元风格"""

    response_received = Signal()  # 收到模型回复时发出

    def __init__(self, parent=None):
        super().__init__(parent)
        self.core = get_core()
        self.conversation_manager = get_conversation_manager()
        self.character_manager = get_character_manager()
        self.memory = get_langchain_memory()
        self.config = get_config()

        self._is_generating = False
        self._scroll_button = None
        self._scroll_anim_opacity = None  # 复用的透明度动画
        self._scroll_anim_scroll = None   # 复用的滚动动画
        self._worker = None
        self._last_user_text = ""  # 用于重新生成
        self._empty_state = None
        self._setup_ui()

        # 根据配置决定是否加载/清空历史
        if self.config.general.keep_conversation_history:
            self._load_history()
        else:
            if self.conversation_manager.messages:
                self.conversation_manager.clear()

        self._check_first_run()
        self._update_empty_state()

        # 延迟滚动到底部（等待布局完成）
        QTimer.singleShot(100, self._scroll_to_bottom)

    def _setup_ui(self):
        """设置 UI - 二次元风格"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 12)
        layout.setSpacing(10)

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

        # 监听滚动位置
        scroll.verticalScrollBar().valueChanged.connect(self._on_scroll_changed)

        layout.addWidget(scroll, 1)
        self._scroll_area = scroll

        # 跳转到最新消息按钮
        self._setup_scroll_to_bottom_button()

        # 空状态占位
        self._empty_state = EmptyStateWidget()
        self._empty_state.setParent(self._scroll_area)
        self._empty_state.hide()

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
        # 延迟设置初始高度，等样式生效后再计算
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

        # 字符计数
        self._char_count_label = QLabel("")
        self._char_count_label.setStyleSheet("color: #aaa; font-size: 10px;")
        bottom_bar.addWidget(self._char_count_label)
        bottom_bar.addStretch()

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

        # 二次元风格样式
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

    def _reset_input_height(self):
        """重置输入框到单行高度"""
        if self.input_edit:
            self.input_edit.setFixedHeight(40)

    def _on_input_text_changed(self):
        """输入内容变化时自适应高度"""
        doc = self.input_edit.document()
        doc_height = doc.size().height()
        margins = self.input_edit.contentsMargins()
        ideal_height = int(doc_height + margins.top() + margins.bottom() + 16)
        clamped = max(40, min(ideal_height, 120))
        if self.input_edit.height() != clamped:
            self.input_edit.setFixedHeight(clamped)
        text = self.input_edit.toPlainText()
        count = len(text)
        if count > 0:
            self._char_count_label.setText(f"{count}")
        else:
            self._char_count_label.setText("")

    def eventFilter(self, obj, event):
        """事件过滤器：Enter 发送，Shift+Enter 换行"""
        if obj is self.input_edit and event.type() == QEvent.Type.KeyPress:
            key_event = event
            if key_event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                if not key_event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                    self._on_send()
                    return True
        return super().eventFilter(obj, event)

    def _on_stop_generate(self):
        """停止生成"""
        if self._worker and self._worker.isRunning():
            self._worker.terminate()
            self._worker.wait(2000)
            logger.info("用户停止了生成")

        if hasattr(self, '_stream_bubble') and self._stream_bubble:
            current_text = self._stream_bubble._text
            if current_text and current_text.strip():
                self._stream_bubble.finalize()
                self.conversation_manager.add_assistant_message(current_text)
            else:
                self._stream_bubble.deleteLater()
            del self._stream_bubble

        self._is_generating = False
        self._update_send_button_state()

    def _update_send_button_state(self):
        """更新发送/停止按钮状态"""
        if self._is_generating:
            self.send_btn.hide()
            self.stop_btn.show()
        else:
            self.send_btn.show()
            self.stop_btn.hide()

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
        """清空所有消息气泡和历史"""
        # 清空 conversation_manager
        self.conversation_manager.clear()

        # 清空 UI 中的消息气泡
        while self.messages_layout.count() > 1:
            item = self.messages_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        self._update_empty_state()
        logger.info("对话已清空")

    def _update_empty_state(self):
        """更新空状态显示"""
        # 有消息时 count > 1（因为有 stretch），无消息时 count == 1
        has_messages = self.messages_layout.count() > 1
        if has_messages:
            self._empty_state.hide()
        else:
            # 居中显示空状态
            self._empty_state.setGeometry(self._scroll_area.rect())
            self._empty_state.show()
            self._empty_state.raise_()

    def resizeEvent(self, event):
        """窗口大小改变时更新按钮位置和气泡宽度"""
        super().resizeEvent(event)
        if self._scroll_button and self._scroll_button.isVisible():
            btn_x = self._scroll_area.width() - self._scroll_button.width() - 10
            btn_y = self._scroll_area.height() - self._scroll_button.height() - 10
            self._scroll_button.move(btn_x, btn_y)
        # 更新空状态位置
        if self._empty_state and self._empty_state.isVisible():
            self._empty_state.setGeometry(self._scroll_area.rect())
        # 更新所有气泡最大宽度
        self._update_all_bubble_widths()

    def _setup_scroll_to_bottom_button(self):
        """设置跳转到最新消息按钮（美化 SVG 图标风格）"""
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
        """滚动位置改变时"""
        scroll_bar = self._scroll_area.verticalScrollBar()
        is_at_bottom = value >= scroll_bar.maximum() - 50

        if is_at_bottom:
            self._hide_scroll_button()
        else:
            self._show_scroll_button()

    def _show_scroll_button(self):
        """显示跳转按钮"""
        if not self._scroll_button.isVisible():
            btn_x = self._scroll_area.width() - self._scroll_button.width() - 10
            btn_y = self._scroll_area.height() - self._scroll_button.height() - 10
            self._scroll_button.move(btn_x, btn_y)
            self._scroll_button.show()

            opacity = self._scroll_button.graphicsEffect()
            if opacity:
                # 停止旧动画
                if self._scroll_anim_opacity and self._scroll_anim_opacity.state() == QPropertyAnimation.State.Running:
                    self._scroll_anim_opacity.stop()
                self._scroll_anim_opacity = QPropertyAnimation(opacity, b"opacity")
                self._scroll_anim_opacity.setDuration(200)
                self._scroll_anim_opacity.setStartValue(0.0)
                self._scroll_anim_opacity.setEndValue(1.0)
                self._scroll_anim_opacity.setEasingCurve(QEasingCurve.Type.OutQuad)
                self._scroll_anim_opacity.start()

    def _hide_scroll_button(self):
        """隐藏跳转按钮"""
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

    def _load_history(self):
        """加载历史消息"""
        messages = self.conversation_manager.messages
        for msg in messages:
            self._add_message_bubble(msg.content, msg.role == "user",
                                     timestamp=msg.timestamp)

    def _check_first_run(self):
        """检查是否是第一次运行，显示引导对话或开场白"""
        persona = self.character_manager.persona

        if self.config.general.keep_conversation_history and self.conversation_manager.messages:
            return

        greeting = self.character_manager.get_random_greeting()

        greeting = greeting.replace("{name}", persona.user_nickname or "你")
        greeting = greeting.replace("{user_nickname}", persona.user_nickname or "你")

        self._add_message_bubble(greeting, is_user=False)

        if persona.is_first_run():
            logger.info("第一次启动，显示引导对话")
        else:
            logger.info("显示开场白")

    def _add_message_bubble(self, text: str, is_user: bool = False,
                            timestamp=None):
        """添加消息气泡"""
        bubble = MessageBubble(text, is_user, timestamp=timestamp)
        # 立即设置气泡最大宽度
        viewport_width = self._scroll_area.viewport().width()
        if viewport_width > 0:
            bubble.update_max_width(viewport_width)
        insert_pos = self.messages_layout.count() - 1
        self.messages_layout.insertWidget(insert_pos, bubble)

        self._update_empty_state()
        QTimer.singleShot(100, self._scroll_to_bottom)

    def _update_all_bubble_widths(self):
        """更新所有气泡的最大宽度（窗口大小变化时调用）"""
        viewport_width = self._scroll_area.viewport().width()
        if viewport_width <= 0:
            return
        for i in range(self.messages_layout.count()):
            item = self.messages_layout.itemAt(i)
            widget = item.widget()
            if isinstance(widget, MessageBubble):
                widget.update_max_width(viewport_width)

    def _scroll_to_bottom(self):
        """平滑滚动到底部"""
        self.messages_container.layout().update()
        self.messages_container.updateGeometry()

        scroll_bar = self._scroll_area.verticalScrollBar()
        target = scroll_bar.maximum()

        # 使用平滑动画滚动
        if self._scroll_anim_scroll and self._scroll_anim_scroll.state() == QPropertyAnimation.State.Running:
            self._scroll_anim_scroll.stop()

        self._scroll_anim_scroll = QPropertyAnimation(scroll_bar, b"value")
        self._scroll_anim_scroll.setDuration(150)
        self._scroll_anim_scroll.setStartValue(scroll_bar.value())
        self._scroll_anim_scroll.setEndValue(target)
        self._scroll_anim_scroll.setEasingCurve(QEasingCurve.Type.OutQuad)
        self._scroll_anim_scroll.start()

        self._hide_scroll_button()

    def _on_send(self):
        """发送消息"""
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

        # 创建流式气泡（带打字指示器）
        self._stream_bubble = MessageBubble("", is_user=False, streaming=True)
        viewport_width = self._scroll_area.viewport().width()
        if viewport_width > 0:
            self._stream_bubble.update_max_width(viewport_width)
        insert_pos = self.messages_layout.count() - 1
        self.messages_layout.insertWidget(insert_pos, self._stream_bubble)

        self._worker = GenerateWorker(user_text, self.core, is_task=is_task)
        self._worker.stream_update.connect(self._on_stream_update)
        self._worker.debug_update.connect(self._on_debug_update)
        self._worker.finished.connect(self._on_response_finished)
        self._worker.error.connect(self._on_response_error)
        self._worker.start()

    def _on_stream_update(self, text: str):
        """流式更新（打字机效果）"""
        if hasattr(self, '_stream_bubble') and self._stream_bubble:
            # 首次收到内容时，显示浏览器、隐藏打字指示器
            if not self._stream_bubble._browser.isVisible() and text:
                self._stream_bubble._browser.show()
                if self._stream_bubble._typing_indicator:
                    self._stream_bubble._typing_indicator.stop()
                    self._stream_bubble._typing_indicator.hide()

            self._stream_bubble.update_text(text)
            # 流式输出时平滑滚动
            scroll_bar = self._scroll_area.verticalScrollBar()
            scroll_bar.setValue(scroll_bar.maximum())

    def _on_debug_update(self, debug_info: dict):
        """调试信息更新 — 工具调用气泡显示在模型回复上方"""
        if self.config.general.chat_mode != "debug":
            return

        debug_type = debug_info.get("debug_type", "")
        debug_title = debug_info.get("debug_title", "")
        debug_content = debug_info.get("debug_content", "")

        if not debug_type or not debug_content:
            return

        debug_bubble = DebugBubble(debug_type, debug_title, debug_content)
        # 插入到流式气泡之前（即模型回复上方）
        if hasattr(self, '_stream_bubble') and self._stream_bubble:
            idx = self.messages_layout.indexOf(self._stream_bubble)
            if idx >= 0:
                self.messages_layout.insertWidget(idx, debug_bubble)
            else:
                insert_pos = self.messages_layout.count() - 1
                self.messages_layout.insertWidget(insert_pos, debug_bubble)
        else:
            insert_pos = self.messages_layout.count() - 1
            self.messages_layout.insertWidget(insert_pos, debug_bubble)

        logger.info(f"显示调试信息: {debug_title}")
        QTimer.singleShot(50, self._scroll_to_bottom)

    def _on_response_finished(self, result: dict):
        """回复生成完成"""
        logger.info(f"_on_response_finished 收到结果: {result}")

        final_text = result.get("final_text", "")
        logger.info(f"final_text: '{final_text}'")

        if final_text:
            if hasattr(self, '_stream_bubble') and self._stream_bubble:
                self._stream_bubble.update_text(final_text)
                self._stream_bubble.finalize()
                self.conversation_manager.add_assistant_message(final_text)
                logger.info(f"流式气泡已 finalize: {final_text[:50]}...")
                del self._stream_bubble
            else:
                self._add_message_bubble(final_text, is_user=False)
                self.conversation_manager.add_assistant_message(final_text)
                logger.info(f"已添加消息气泡: {final_text[:50]}...")
        else:
            if hasattr(self, '_stream_bubble'):
                self._stream_bubble.deleteLater()
                del self._stream_bubble
            logger.warning("final_text 为空!")

        self._is_generating = False
        self._update_send_button_state()
        self._update_empty_state()

        self.response_received.emit()
        logger.info("回复生成完成")

    def _on_response_error(self, error: str):
        """回复生成错误"""
        if hasattr(self, '_stream_bubble'):
            self._stream_bubble.deleteLater()
            del self._stream_bubble

        error_msg = f"抱歉，出错了：{error}"
        self._add_message_bubble(error_msg, is_user=False)

        self._is_generating = False
        self._update_send_button_state()

        logger.error(f"回复生成失败: {error}")

    def _regenerate_last_response(self):
        """重新生成最后一条 AI 回复"""
        if self._is_generating:
            return
        if not self._last_user_text:
            return

        # 移除最后一条 AI 消息
        if self.conversation_manager.messages and self.conversation_manager.messages[-1].role == "assistant":
            self.conversation_manager.messages.pop()
            self.conversation_manager._save()

        # 移除最后一个 AI 气泡
        count = self.messages_layout.count()
        if count >= 2:
            last_widget = self.messages_layout.itemAt(count - 2).widget()
            if last_widget and isinstance(last_widget, MessageBubble) and not last_widget._is_user:
                last_widget.deleteLater()

        self._generate_response(self._last_user_text)


class GenerateWorker(QThread):
    """生成回复的后台线程 - 使用 LangChain Agent"""

    stream_update = Signal(str)
    debug_update = Signal(dict)
    finished = Signal(dict)
    error = Signal(str)

    _event_loop = None

    def __init__(self, user_text: str, core, is_task: bool = False):
        super().__init__()
        self.user_text = user_text
        self.core = core
        self.is_task = is_task

    @classmethod
    def _get_event_loop(cls):
        """获取或创建持久的事件循环"""
        if cls._event_loop is None or cls._event_loop.is_closed():
            cls._event_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(cls._event_loop)
        return cls._event_loop

    def run(self):
        """执行"""
        try:
            loop = self._get_event_loop()
            result = loop.run_until_complete(
                self._generate_with_agent()
            )
            self.finished.emit(result)
        except Exception as e:
            logger.error(f"生成回复失败: {e}", exc_info=True)
            self.error.emit(str(e))

    async def _generate_with_agent(self):
        """使用 LangChain Agent 生成回复"""
        full_text = ""

        async for response in self.core.chat(self.user_text, stream=True):
            if response.content:
                full_text += response.content
                self.stream_update.emit(full_text)

            if response.debug_type:
                self.debug_update.emit({
                    "debug_type": response.debug_type,
                    "debug_title": response.debug_title or "",
                    "debug_content": response.debug_content or ""
                })

        return {"final_text": full_text, "is_task": self.is_task}
