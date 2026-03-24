# Chat Widget
import sys
import asyncio
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
from chat.conversation_manager import get_conversation_manager
from agent import get_core, get_langchain_memory
from utils import get_character_manager, get_logger

logger = get_logger()


class ChatWidget(QFrame):
    """对话窗口"""
    
    response_received = Signal()  # 收到模型回复时发出

    def __init__(self, parent=None):
        super().__init__(parent)
        # 使用新的 LangChain Agent
        self.core = get_core()
        self.conversation_manager = get_conversation_manager()
        self.character_manager = get_character_manager()
        self.memory = get_langchain_memory()
        
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
        """检查是否是第一次运行，显示引导对话或开场白"""
        persona = self.character_manager.persona
        
        # 如果有对话历史，不显示开场白
        if self.conversation_manager.messages:
            return
        
        # 获取问候语并处理模板变量
        greeting = self.character_manager.get_random_greeting()
        
        # 替换模板变量
        greeting = greeting.replace("{name}", persona.user_nickname or "你")
        greeting = greeting.replace("{user_nickname}", persona.user_nickname or "你")
        
        self._add_message_bubble(greeting, is_user=False)
        
        if persona.is_first_run():
            logger.info("第一次启动，显示引导对话")
        else:
            logger.info("显示开场白")

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

        # 启动后台线程生成 - 使用新的 LangChain Agent
        self._worker = GenerateWorker(user_text, self.core)
        self._worker.stream_update.connect(self._on_stream_update)
        self._worker.finished.connect(self._on_response_finished)
        self._worker.error.connect(self._on_response_error)
        self._worker.start()

    def _on_stream_update(self, text: str):
        """流式更新（打字机效果）"""
        # logger.info(f"_on_stream_update: {text[:50] if text else '空'}...")
        if hasattr(self, '_stream_bubble') and self._stream_bubble:
            # 更新流式气泡内容
            self._stream_bubble.update_text(text)
            self._scroll_to_bottom()

    def _on_response_finished(self, result: dict):
        """回复生成完成"""
        logger.info(f"_on_response_finished 收到结果: {result}")
        
        # 移除流式气泡（如果有）
        if hasattr(self, '_stream_bubble'):
            self._stream_bubble.deleteLater()
            del self._stream_bubble

        final_text = result.get("final_text", "")
        logger.info(f"final_text: '{final_text}'")
        
        if final_text:
            self._add_message_bubble(final_text, is_user=False)
            self.conversation_manager.add_assistant_message(final_text)
            logger.info(f"已添加消息气泡: {final_text[:50]}...")
        else:
            logger.warning("final_text 为空!")

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
    """生成回复的后台线程 - 使用 LangChain Agent"""

    stream_update = Signal(str)
    finished = Signal(dict)
    error = Signal(str)

    # 类级别的事件循环，保持持久运行
    _event_loop = None

    def __init__(self, user_text: str, core):
        super().__init__()
        self.user_text = user_text
        self.core = core  # AIFriendCore 实例

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
            # 使用持久的事件循环，不关闭
            loop = self._get_event_loop()

            # 运行异步生成流程
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
        
        return {"final_text": full_text}
