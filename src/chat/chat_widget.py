# Chat Widget
import sys
import asyncio
from pathlib import Path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLineEdit, QPushButton, QScrollArea,
    QFrame, QLabel, QGraphicsOpacityEffect, QApplication
)
from PySide6.QtCore import Qt, Signal, QThread, QEventLoop, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtGui import QFont, QColor

from chat.message_bubble import MessageBubble
from chat.debug_bubble import DebugBubble
from chat.conversation_manager import get_conversation_manager
from agent import get_core, get_langchain_memory
from utils import get_character_manager, get_logger, get_config

logger = get_logger()


class ChatWidget(QFrame):
    """对话窗口 - 二次元风格"""
    
    response_received = Signal()  # 收到模型回复时发出

    def __init__(self, parent=None):
        super().__init__(parent)
        # 使用新的 LangChain Agent
        self.core = get_core()
        self.conversation_manager = get_conversation_manager()
        self.character_manager = get_character_manager()
        self.memory = get_langchain_memory()
        self.config = get_config()
        
        self._is_generating = False
        self._scroll_button = None
        self._scroll_animation = None
        self._setup_ui()
        self._load_history()
        self._check_first_run()
        
        # 延迟滚动到底部（等待布局完成）
        QTimer.singleShot(100, self._scroll_to_bottom)

    def _setup_ui(self):
        """设置 UI - 二次元风格"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # 标题栏（移除，改为在 ChatBubbleWindow 中统一管理）
        # 这样可以让布局更紧凑

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

        # 跳转到最新消息按钮（浮动按钮）
        self._setup_scroll_to_bottom_button()

        # 输入区
        input_layout = QHBoxLayout()
        input_layout.setSpacing(8)

        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("✨ 输入消息... (Enter 发送)")
        self.input_edit.setFont(QFont("Arial", 11))
        self.input_edit.returnPressed.connect(self._on_send)
        input_layout.addWidget(self.input_edit, 1)

        self.send_btn = QPushButton("✈️ 发送")
        self.send_btn.setMinimumWidth(75)
        self.send_btn.clicked.connect(self._on_send)
        input_layout.addWidget(self.send_btn)

        layout.addLayout(input_layout)

        # 二次元风格样式
        self.setStyleSheet("""
            ChatWidget {
                background-color: transparent;
                border: none;
            }
            QLineEdit {
                padding: 10px 15px;
                border: 2px solid #B8D4FF;
                border-radius: 22px;
                background-color: white;
                color: #555;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #7BB8FF;
                background-color: #F8FBFF;
            }
            QLineEdit:hover {
                border-color: #9BC8FF;
            }
            QPushButton#sendBtn {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #A8D8FF, stop:1 #7BB8FF);
                color: white;
                border: none;
                border-radius: 22px;
                padding: 10px 18px;
                font-weight: bold;
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
        """)
        
        self.send_btn.setObjectName("sendBtn")
    
    def _setup_scroll_to_bottom_button(self):
        """设置跳转到最新消息按钮"""
        self._scroll_button = QPushButton("⬇")
        self._scroll_button.setObjectName("scrollBtn")
        self._scroll_button.setFixedSize(40, 40)
        self._scroll_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._scroll_button.setStyleSheet("""
            QPushButton#scrollBtn {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #A8D8FF, stop:1 #7BB8FF);
                color: white;
                border: none;
                border-radius: 20px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton#scrollBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #B8E8FF, stop:1 #8BC8FF);
            }
            QPushButton#scrollBtn:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #8BC8FF, stop:1 #6BA8FF);
            }
        """)
        self._scroll_button.clicked.connect(self._scroll_to_bottom)
        
        # 添加透明度效果
        opacity_effect = QGraphicsOpacityEffect(self._scroll_button)
        opacity_effect.setOpacity(0.0)
        self._scroll_button.setGraphicsEffect(opacity_effect)
        
        # 将按钮添加到滚动区域（作为浮动按钮）
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
            # 计算按钮位置（右下角）
            btn_x = self._scroll_area.width() - self._scroll_button.width() - 10
            btn_y = self._scroll_area.height() - self._scroll_button.height() - 10
            self._scroll_button.move(btn_x, btn_y)
            self._scroll_button.show()
            
            # 淡入动画
            opacity = self._scroll_button.graphicsEffect()
            if opacity:
                self._scroll_animation = QPropertyAnimation(opacity, b"opacity")
                self._scroll_animation.setDuration(200)
                self._scroll_animation.setStartValue(0.0)
                self._scroll_animation.setEndValue(1.0)
                self._scroll_animation.setEasingCurve(QEasingCurve.Type.OutQuad)
                self._scroll_animation.start()
    
    def resizeEvent(self, event):
        """窗口大小改变时更新按钮位置"""
        super().resizeEvent(event)
        if self._scroll_button and self._scroll_button.isVisible():
            btn_x = self._scroll_area.width() - self._scroll_button.width() - 10
            btn_y = self._scroll_area.height() - self._scroll_button.height() - 10
            self._scroll_button.move(btn_x, btn_y)
    
    def _hide_scroll_button(self):
        """隐藏跳转按钮"""
        if self._scroll_button.isVisible():
            opacity = self._scroll_button.graphicsEffect()
            if opacity:
                self._scroll_animation = QPropertyAnimation(opacity, b"opacity")
                self._scroll_animation.setDuration(150)
                self._scroll_animation.setStartValue(1.0)
                self._scroll_animation.setEndValue(0.0)
                self._scroll_animation.setEasingCurve(QEasingCurve.Type.InQuad)
                self._scroll_animation.finished.connect(self._scroll_button.hide)
                self._scroll_animation.start()
            else:
                self._scroll_button.hide()

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

        # 滚动到底部（延迟确保布局完成）
        QTimer.singleShot(100, self._scroll_to_bottom)

    def _scroll_to_bottom(self):
        """滚动到底部"""
        # 强制更新布局
        self.messages_container.layout().update()
        self.messages_container.updateGeometry()
        QApplication.processEvents()
        
        # 直接滚动到底部
        scroll_bar = self._scroll_area.verticalScrollBar()
        scroll_bar.setValue(scroll_bar.maximum())
        
        # 隐藏跳转按钮
        self._hide_scroll_button()

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

    def _generate_response(self, user_text: str, is_task: bool = False):
        """生成回复

        Args:
            user_text: 用户输入文本
            is_task: 是否为任务触发（任务触发时不添加用户消息到历史）
        """
        self._is_generating = True
        self.send_btn.setEnabled(False)
        self.send_btn.setText("生成中...")

        # 创建流式气泡（占位）
        self._stream_bubble = MessageBubble("", is_user=False)
        insert_pos = self.messages_layout.count() - 1
        self.messages_layout.insertWidget(insert_pos, self._stream_bubble)

        # 启动后台线程生成 - 使用新的 LangChain Agent
        self._worker = GenerateWorker(user_text, self.core, is_task=is_task)
        self._worker.stream_update.connect(self._on_stream_update)
        self._worker.debug_update.connect(self._on_debug_update)
        self._worker.finished.connect(self._on_response_finished)
        self._worker.error.connect(self._on_response_error)
        self._worker.start()

    def _on_stream_update(self, text: str):
        """流式更新（打字机效果）"""
        # logger.info(f"_on_stream_update: {text[:50] if text else '空'}...")
        if hasattr(self, '_stream_bubble') and self._stream_bubble:
            # 更新流式气泡内容
            self._stream_bubble.update_text(text)
            # 流式输出时直接滚动（不用动画）
            scroll_bar = self._scroll_area.verticalScrollBar()
            scroll_bar.setValue(scroll_bar.maximum())
    
    def _on_debug_update(self, debug_info: dict):
        """调试信息更新"""
        # 检查是否为调试模式
        if self.config.general.chat_mode != "debug":
            return
        
        debug_type = debug_info.get("debug_type", "")
        debug_title = debug_info.get("debug_title", "")
        debug_content = debug_info.get("debug_content", "")
        
        if not debug_type or not debug_content:
            return
        
        # 创建调试气泡
        debug_bubble = DebugBubble(debug_type, debug_title, debug_content)
        insert_pos = self.messages_layout.count() - 1
        self.messages_layout.insertWidget(insert_pos, debug_bubble)
        
        logger.info(f"显示调试信息: {debug_title}")
        # 延迟滚动确保布局更新
        QTimer.singleShot(50, self._scroll_to_bottom)

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

    stream_update = Signal(str)  # 文本内容
    debug_update = Signal(dict)  # 调试信息
    finished = Signal(dict)
    error = Signal(str)

    # 类级别的事件循环，保持持久运行
    _event_loop = None

    def __init__(self, user_text: str, core, is_task: bool = False):
        super().__init__()
        self.user_text = user_text
        self.core = core  # AIFriendCore 实例
        self.is_task = is_task  # 是否为任务触发

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

            # 发送调试信息
            if response.debug_type:
                self.debug_update.emit({
                    "debug_type": response.debug_type,
                    "debug_title": response.debug_title or "",
                    "debug_content": response.debug_content or ""
                })

        return {"final_text": full_text, "is_task": self.is_task}
