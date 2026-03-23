# Chat Widget
import sys
from pathlib import Path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLineEdit, QPushButton, QScrollArea,
    QFrame, QLabel
)
from PySide6.QtCore import Qt, Signal, QThread, QEventLoop
from PySide6.QtGui import QFont

from chat.message_bubble import MessageBubble
from chat.llm_client import get_llm_client
from chat.conversation_manager import get_conversation_manager
from utils import get_character_manager, get_logger

logger = get_logger()


class ChatWidget(QFrame):
    """对话窗口"""
    
    response_received = Signal()  # 收到模型回复时发出

    def __init__(self, parent=None):
        super().__init__(parent)
        self.llm_client = get_llm_client()
        self.conversation_manager = get_conversation_manager()
        self.character_manager = get_character_manager()
        self._is_generating = False
        self._setup_ui()
        self._load_history()
        self._check_first_run()

    def _setup_ui(self):
        """设置 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 标题
        title = QLabel("💬 对话")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title)

        # 消息列表滚动区
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea { border: none; background-color: transparent; }
        """)

        self.messages_container = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.setSpacing(8)
        self.messages_layout.addStretch()
        scroll.setWidget(self.messages_container)

        layout.addWidget(scroll, 1)
        self._scroll_area = scroll

        # 输入区
        input_layout = QHBoxLayout()

        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("输入消息... (Enter 发送, Shift+Enter 换行)")
        self.input_edit.setFont(QFont("Arial", 12))
        self.input_edit.returnPressed.connect(self._on_send)
        input_layout.addWidget(self.input_edit, 1)

        self.send_btn = QPushButton("发送")
        self.send_btn.setMinimumWidth(80)
        self.send_btn.clicked.connect(self._on_send)
        input_layout.addWidget(self.send_btn)

        layout.addLayout(input_layout)

        # 样式
        self.setStyleSheet("""
            ChatWidget {
                background-color: rgba(255, 255, 255, 240);
                border-radius: 12px;
            }
            QLineEdit {
                padding: 10px;
                border: 2px solid #E0E0E0;
                border-radius: 20px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #007AFF;
            }
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 20px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056CC;
            }
            QPushButton:pressed {
                background-color: #004499;
            }
            QPushButton:disabled {
                background-color: #CCCCCC;
            }
        """)

    def _load_history(self):
        """加载历史消息"""
        messages = self.conversation_manager.messages
        for msg in messages:
            self._add_message_bubble(msg.content, msg.role == "user")

    def _check_first_run(self):
        """检查是否是第一次运行，显示引导对话"""
        if self.character_manager.persona.is_first_run():
            # 第一次运行，显示引导对话
            greeting = self.character_manager.get_random_greeting()
            self._add_message_bubble(greeting, is_user=False)
            logger.info("第一次启动，显示引导对话")

    def _add_message_bubble(self, text: str, is_user: bool = False):
        """添加消息气泡"""
        bubble = MessageBubble(text, is_user)
        insert_pos = self.messages_layout.count() - 1
        self.messages_layout.insertWidget(insert_pos, bubble)

        # 滚动到底部
        self._scroll_to_bottom()

    def _scroll_to_bottom(self):
        """滚动到底部"""
        scroll_bar = self._scroll_area.verticalScrollBar()
        scroll_bar.setValue(scroll_bar.maximum())

    def _on_send(self):
        """发送消息"""
        if self._is_generating:
            return

        text = self.input_edit.text().strip()
        if not text:
            return

        # 添加用户消息
        self._add_message_bubble(text, is_user=True)
        self.conversation_manager.add_user_message(text)
        self.input_edit.clear()

        # 生成回复
        self._generate_response(text)

    def _generate_response(self, user_text: str):
        """生成回复"""
        self._is_generating = True
        self.send_btn.setEnabled(False)
        self.send_btn.setText("生成中...")

        # 创建流式气泡（占位）
        self._stream_bubble = MessageBubble("", is_user=False)
        insert_pos = self.messages_layout.count() - 1
        self.messages_layout.insertWidget(insert_pos, self._stream_bubble)

        # 启动后台线程生成
        self._worker = GenerateWorker(
            user_text,
            self.llm_client,
            self.conversation_manager
        )
        self._worker.stream_update.connect(self._on_stream_update)
        self._worker.finished.connect(self._on_response_finished)
        self._worker.error.connect(self._on_response_error)
        self._worker.tool_calls.connect(self._on_tool_calls)
        self._worker.start()

    def _on_stream_update(self, text: str):
        """流式更新（打字机效果）"""
        if hasattr(self, '_stream_bubble'):
            # 更新流式气泡内容
            self._stream_bubble.update_text(text)

    def _on_tool_calls(self, tool_calls_info: str):
        """工具调用信息显示"""
        # 显示工具调用信息
        info_bubble = MessageBubble(f"🔧 {tool_calls_info}", is_user=False)
        insert_pos = self.messages_layout.count() - 1
        self.messages_layout.insertWidget(insert_pos, info_bubble)
        self._scroll_to_bottom()

    def _on_response_finished(self, result: dict):
        """回复生成完成"""
        # 移除流式气泡（如果有）
        if hasattr(self, '_stream_bubble'):
            self._stream_bubble.deleteLater()

        final_text = result.get("final_text", "")
        if final_text:
            self._add_message_bubble(final_text, is_user=False)
            self.conversation_manager.add_assistant_message(final_text)

        self._is_generating = False
        self.send_btn.setEnabled(True)
        self.send_btn.setText("发送")

        # 发出收到回复的信号
        self.response_received.emit()
        logger.info("回复生成完成")

    def _on_response_error(self, error: str):
        """回复生成错误"""
        # 移除流式气泡（如果有）
        if hasattr(self, '_stream_bubble'):
            self._stream_bubble.deleteLater()

        error_msg = f"抱歉，出错了：{error}"
        self._add_message_bubble(error_msg, is_user=False)

        self._is_generating = False
        self.send_btn.setEnabled(True)
        self.send_btn.setText("发送")

        logger.error(f"回复生成失败: {error}")


class GenerateWorker(QThread):
    """生成回复的后台线程 - 支持流式输出和 Function Calling"""

    stream_update = Signal(str)
    finished = Signal(dict)
    error = Signal(str)
    tool_calls = Signal(str)

    def __init__(self, user_text: str, llm_client, conversation_manager):
        super().__init__()
        self.user_text = user_text
        self.llm_client = llm_client
        self.conversation_manager = conversation_manager

    def run(self):
        """执行"""
        try:
            import asyncio
            from assistant.function_calling import get_function_handler

            # 创建新的事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                # 运行异步生成流程
                result = loop.run_until_complete(
                    self._generate_with_function_calling()
                )
                self.finished.emit(result)
            finally:
                loop.close()

        except Exception as e:
            logger.error(f"生成回复失败: {e}")
            self.error.emit(str(e))

    async def _generate_with_function_calling(self):
        """使用 Function Calling 生成回复"""
        from assistant.function_calling import get_function_handler

        handler = get_function_handler()

        # 第一轮：调用 LLM，检测是否需要调用工具
        messages = self.conversation_manager.get_recent_messages()

        response = await self.llm_client.chat(
            messages,
            tools=handler.get_tools(),
            stream=False  # 非流式，方便检测 tool_calls
        )

        if not hasattr(response, 'choices') or not response.choices:
            return {"final_text": "抱歉，我没有理解。"}

        message = response.choices[0].message

        # 检查是否有 tool_calls
        if hasattr(message, 'tool_calls') and message.tool_calls:
            # 处理工具调用
            needs_confirm, tool_results = await handler.process_tool_calls(message)

            # 显示工具调用信息
            tool_calls_info = []
            for tc in message.tool_calls:
                tool_calls_info.append(f"调用: {tc.function.name}")
            self.tool_calls.emit("\n".join(tool_calls_info))

            # 如果需要确认
            if needs_confirm:
                return {"final_text": needs_confirm}

            # 第二轮：使用流式输出，传递工具结果
            messages.append({
                "role": "assistant",
                "content": message.content or ""
            })
            messages.extend(tool_results)

            # 流式输出最终回复
            full_text = ""
            async for chunk in await self.llm_client.chat(
                messages,
                tools=handler.get_tools(),
                stream=True
            ):
                full_text += chunk
                self.stream_update.emit(full_text)

            return {"final_text": full_text}
        else:
            # 没有工具调用，直接流式输出回复
            full_text = ""
            async for chunk in await self.llm_client.chat(
                messages,
                tools=handler.get_tools(),
                stream=True
            ):
                full_text += chunk
                self.stream_update.emit(full_text)

            return {"final_text": full_text}
