# LangChain Agent - 基于 LangGraph 的智能体
from typing import List, Optional, Dict, Any, AsyncGenerator
from dataclasses import dataclass, field

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.tools import StructuredTool
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

from agent.models import create_chat_model, get_llm_config
from agent.tools.registry import get_tool_registry
from agent.memory import get_langchain_memory
from agent.prompts import get_agent_prompt, build_system_prompt
from utils import get_logger

logger = get_logger()


@dataclass
class ChatResponse:
    """对话响应"""
    content: str
    role: str = "assistant"
    tool_calls: List[Dict] = field(default_factory=list)
    skill_triggered: Optional[str] = None
    metadata: Dict = field(default_factory=dict)


class AIFriendAgent:
    """基于 LangGraph 的智能体
    
    特性：
    - 自动工具调用（LangGraph 自动处理）
    - 流式输出支持
    - 与现有 MemoryManager 兼容
    """
    
    def __init__(
        self,
        llm: Optional[BaseChatModel] = None,
        tools: Optional[List[StructuredTool]] = None,
    ):
        # 创建或使用提供的 LLM
        self.llm = llm or self._create_default_llm()
        
        # 获取工具
        self.tools = tools or self._get_default_tools()
        
        # 获取记忆
        self.memory = get_langchain_memory()
        
        # 系统提示词
        self._system_prompt = None
        
        # 创建 Agent
        self._checkpointer = MemorySaver()
        self._agent = self._create_agent()
        
        logger.info(f"LangGraph Agent 初始化完成，工具数: {len(self.tools)}")
    
    def _create_agent(self):
        """创建 LangGraph Agent"""
        system_prompt = build_system_prompt()
        return create_react_agent(
            model=self.llm,
            tools=self.tools,
            checkpointer=self._checkpointer,
            prompt=system_prompt,
        )
    
    def _create_default_llm(self) -> BaseChatModel:
        """创建默认 LLM"""
        from agent.models.factory import get_default_chat_model
        return get_default_chat_model()
    
    def _get_default_tools(self) -> List[StructuredTool]:
        """获取默认工具"""
        registry = get_tool_registry()
        return registry.get_tools_for_agent()
    
    async def chat(
        self,
        user_input: str,
        stream: bool = True
    ) -> AsyncGenerator[ChatResponse, None]:
        """处理用户输入
        
        Args:
            user_input: 用户输入
            stream: 是否流式输出
            
        Yields:
            ChatResponse 响应
        """
        logger.info(f"处理用户输入: {user_input[:50]}...")
        
        # 获取历史消息
        messages = self.memory.get_messages()
        
        # 添加用户消息
        messages = list(messages) + [HumanMessage(content=user_input)]
        
        # 配置
        config = {"configurable": {"thread_id": "default"}}
        
        if stream:
            # 流式输出
            async for response in self._chat_stream(messages, config):
                yield response
        else:
            # 非流式输出
            result = await self._agent.ainvoke(
                {"messages": messages},
                config=config
            )
            
            # 获取最后一条 AI 消息
            output = ""
            for msg in reversed(result.get("messages", [])):
                if isinstance(msg, AIMessage):
                    output = msg.content
                    break
            
            # 保存到记忆
            self.memory.add_user_message(user_input)
            self.memory.add_ai_message(output)
            
            yield ChatResponse(content=output)
    
    async def _chat_stream(
        self,
        messages: List[BaseMessage],
        config: Dict
    ) -> AsyncGenerator[ChatResponse, None]:
        """流式对话"""
        full_content = ""
        
        try:
            async for event in self._agent.astream_events(
                {"messages": messages},
                config=config,
                version="v2",
            ):
                event_type = event.get("event")
                
                # LLM 输出 token
                if event_type == "on_chat_model_stream":
                    chunk = event.get("data", {}).get("chunk")
                    if chunk and hasattr(chunk, "content") and chunk.content:
                        token = chunk.content
                        full_content += token
                        yield ChatResponse(content=token)
                
                # 工具调用开始
                elif event_type == "on_tool_start":
                    tool_name = event.get("name", "")
                    logger.info(f"工具调用开始: {tool_name}")
                
                # 工具调用结束
                elif event_type == "on_tool_end":
                    tool_name = event.get("name", "")
                    logger.info(f"工具调用结束: {tool_name}")
            
            # 保存到记忆
            if messages:
                user_msg = messages[-1]
                if isinstance(user_msg, HumanMessage):
                    self.memory.add_user_message(user_msg.content)
            if full_content:
                self.memory.add_ai_message(full_content)
            
            # 如果没有收集到内容，尝试获取最终输出
            if not full_content:
                result = await self._agent.ainvoke(
                    {"messages": messages},
                    config=config
                )
                for msg in reversed(result.get("messages", [])):
                    if isinstance(msg, AIMessage):
                        full_content = msg.content
                        self.memory.add_ai_message(full_content)
                        yield ChatResponse(content=full_content)
                        break
                    
        except Exception as e:
            logger.error(f"Agent 执行错误: {e}", exc_info=True)
            yield ChatResponse(content=f"抱歉，处理时出现错误：{str(e)}")
    
    async def chat_with_history(
        self,
        user_input: str,
        history: List[Dict[str, str]],
        stream: bool = True
    ) -> AsyncGenerator[ChatResponse, None]:
        """带历史的对话
        
        Args:
            user_input: 用户输入
            history: 对话历史 [{"role": "user/assistant", "content": "..."}]
            stream: 是否流式输出
            
        Yields:
            ChatResponse 响应
        """
        # 清空当前记忆
        self.memory.clear()
        
        # 添加历史消息
        for msg in history:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role == "user":
                self.memory.add_user_message(content)
            elif role == "assistant":
                self.memory.add_ai_message(content)
        
        # 执行对话
        async for response in self.chat(user_input, stream):
            yield response
    
    def update_tools(self, tools: List[StructuredTool]):
        """更新工具列表"""
        self.tools = tools
        self._agent = self._create_agent()
        logger.info(f"工具已更新，数量: {len(self.tools)}")
    
    def update_llm(self, llm: BaseChatModel):
        """更新 LLM"""
        self.llm = llm
        self._agent = self._create_agent()
        logger.info("LLM 已更新")


# 全局 Agent 实例
_agent: Optional[AIFriendAgent] = None


def get_agent() -> AIFriendAgent:
    """获取全局 Agent 实例"""
    global _agent
    if _agent is None:
        _agent = AIFriendAgent()
    return _agent


def reset_agent():
    """重置 Agent 实例"""
    global _agent
    _agent = None
