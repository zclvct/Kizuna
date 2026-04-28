# Base Agent - Agent 抽象基类与共享数据类
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, AsyncGenerator, Optional, Dict

from langchain_core.tools import StructuredTool
from langchain_core.language_models.chat_models import BaseChatModel


@dataclass
class ChatResponse:
    """对话响应"""
    content: str
    role: str = "assistant"
    tool_calls: List[Dict] = field(default_factory=list)
    skill_triggered: Optional[str] = None
    metadata: Dict = field(default_factory=dict)
    # 调试信息
    debug_type: Optional[str] = None  # tool_call, tool_result, thought
    debug_title: Optional[str] = None
    debug_content: Optional[str] = None


class BaseAgent(ABC):
    """Agent 抽象基类

    定义所有 Agent 实现必须提供的接口，
    确保上层 AIFriendCore 和 ChatWidget 无感知切换。
    """

    @abstractmethod
    async def chat(
        self,
        user_input: str,
        stream: bool = True
    ) -> AsyncGenerator[ChatResponse, None]:
        """处理用户输入，流式返回响应

        Args:
            user_input: 用户输入文本
            stream: 是否流式输出

        Yields:
            ChatResponse 响应（文本 token / 工具调用调试信息）
        """

    @abstractmethod
    def update_tools(self, tools: List[StructuredTool]):
        """更新工具列表"""

    @abstractmethod
    def update_llm(self, llm: BaseChatModel):
        """更新 LLM（LangChain 模式使用，Pure 模式可忽略）"""

    @abstractmethod
    async def chat_with_history(
        self,
        user_input: str,
        history: List[Dict[str, str]],
        stream: bool = True
    ) -> AsyncGenerator[ChatResponse, None]:
        """带历史的对话"""
