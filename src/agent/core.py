# AIFriend Core - 统一入口
from typing import Optional, List, Dict, Any, AsyncGenerator
from dataclasses import dataclass, field

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.tools import StructuredTool

from agent.models import LLMConfig, create_chat_model, get_llm_config
from agent.tools.registry import get_tool_registry
from agent.memory import get_langchain_memory
from agent.agent import AIFriendAgent, ChatResponse, get_agent
from agent.prompts import build_system_prompt
from agent.config import get_app_config
from utils import get_logger

logger = get_logger()


@dataclass
class ChatResult:
    """对话结果"""
    content: str
    tool_calls: List[Dict] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)


class AIFriendCore:
    """AI Friend 核心类
    
    统一入口，封装所有功能：
    - 模型管理
    - 工具管理
    - 记忆管理
    - Agent 执行
    """
    
    def __init__(self):
        # 加载配置
        self.config = get_app_config()
        
        # 创建模型
        self.llm = self._create_llm()
        
        # 获取工具
        self.tools = self._get_tools()
        
        # 获取记忆
        self.memory = get_langchain_memory()
        
        # 创建 Agent
        self.agent = AIFriendAgent(
            llm=self.llm,
            tools=self.tools,
        )
        
        logger.info("AIFriendCore 初始化完成")
    
    def _create_llm(self) -> BaseChatModel:
        """创建 LLM"""
        llm_config = self.config.llm
        provider_config = llm_config.get_provider_config()
        return create_chat_model(provider_config)
    
    def _get_tools(self) -> List[StructuredTool]:
        """获取启用的工具"""
        registry = get_tool_registry()
        return registry.get_tools_for_agent()
    
    async def chat(
        self,
        user_input: str,
        stream: bool = True
    ) -> AsyncGenerator[ChatResponse, None]:
        """处理对话
        
        Args:
            user_input: 用户输入
            stream: 是否流式输出
            
        Yields:
            ChatResponse 响应
        """
        async for response in self.agent.chat(user_input, stream):
            yield response
    
    def switch_provider(self, provider_name: str):
        """切换 LLM 提供商
        
        Args:
            provider_name: 提供商配置名称
        """
        llm_config = self.config.llm
        provider_config = llm_config.get_provider_config(provider_name)
        new_llm = create_chat_model(provider_config)
        
        self.llm = new_llm
        self.agent.update_llm(new_llm)
        
        logger.info(f"已切换到 LLM 提供商: {provider_name}")
    
    def reload_tools(self):
        """重新加载工具"""
        self.tools = self._get_tools()
        self.agent.update_tools(self.tools)
        logger.info("工具已重新加载")
    
    def clear_memory(self):
        """清空记忆"""
        self.memory.clear()
        logger.info("记忆已清空")
    
    def get_enabled_tool_names(self) -> List[str]:
        """获取启用的工具名称列表"""
        return [tool.name for tool in self.tools]


# 全局实例
_core: Optional[AIFriendCore] = None


def get_core() -> AIFriendCore:
    """获取全局 Core 实例"""
    global _core
    if _core is None:
        _core = AIFriendCore()
    return _core


def reset_core():
    """重置 Core 实例"""
    global _core
    _core = None
