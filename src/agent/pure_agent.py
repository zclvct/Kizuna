# Pure Python Agent - 基于 litellm 的纯 Python ReAct 智能体
from typing import List, AsyncGenerator, Optional, Dict

import litellm
from langchain_core.tools import StructuredTool
from langchain_core.language_models.chat_models import BaseChatModel

from agent.base_agent import BaseAgent, ChatResponse
from agent.memory import get_langchain_memory
from agent.prompts import build_system_prompt
from agent.pure_tools import structured_tools_to_litellm, execute_tool_call
from agent.models.config import LLMProviderConfig
from utils import get_logger

logger = get_logger()

MAX_REACT_STEPS = 10  # 防止无限循环

# provider → litellm model 前缀
PROVIDER_PREFIX = {
    "openai": "openai/",
    "anthropic": "anthropic/",
    "deepseek": "deepseek/",
    "ollama": "ollama/",
}


class PurePythonAgent(BaseAgent):
    """纯 Python 实现的 ReAct Agent

    使用 litellm 统一调用所有 LLM 提供商，
    手动实现 ReAct 推理循环（思考 → 工具调用 → 观察 → 继续思考）。
    """

    def __init__(
        self,
        llm_config: Optional[LLMProviderConfig] = None,
        tools: Optional[List[StructuredTool]] = None,
    ):
        self.llm_config = llm_config or self._get_default_config()
        self.tools = tools or self._get_default_tools()
        self.memory = get_langchain_memory()
        self._system_prompt = build_system_prompt()

        # 构建 litellm 工具 schema
        self._tool_schemas = structured_tools_to_litellm(self.tools)
        # 工具名 → StructuredTool 映射
        self._tool_map: Dict[str, StructuredTool] = {t.name: t for t in self.tools}

        # 配置 litellm
        self._setup_litellm()

        logger.info(f"PurePythonAgent 初始化完成，工具数: {len(self.tools)}")

    def _setup_litellm(self):
        """配置 litellm 全局设置"""
        litellm.suppress_debug_info = True
        # 关闭 litellm 的冗余日志
        litellm.set_verbose = False

        # 设置 API Key（根据 provider 设置环境变量，litellm 自动读取）
        if self.llm_config.api_key:
            import os
            provider = self.llm_config.provider
            if provider == "openai":
                os.environ.setdefault("OPENAI_API_KEY", self.llm_config.api_key)
            elif provider == "anthropic":
                os.environ.setdefault("ANTHROPIC_API_KEY", self.llm_config.api_key)
            elif provider == "deepseek":
                os.environ.setdefault("DEEPSEEK_API_KEY", self.llm_config.api_key)

    def _get_litellm_model(self) -> str:
        """将 LLMProviderConfig 转换为 litellm model 字符串"""
        provider = self.llm_config.provider
        model = self.llm_config.model
        prefix = PROVIDER_PREFIX.get(provider, "openai/")
        return f"{prefix}{model}"

    def _get_default_config(self) -> LLMProviderConfig:
        from agent.models.factory import get_llm_config
        config = get_llm_config()
        return config.get_provider_config()

    def _get_default_tools(self) -> List[StructuredTool]:
        from agent.tools.registry import get_tool_registry
        return get_tool_registry().get_tools_for_agent()

    def _build_messages(self, user_input: str) -> List[dict]:
        """构建发送给 litellm 的 messages 列表"""
        messages = []

        # 1. 系统提示词
        messages.append({
            "role": "system",
            "content": self._system_prompt
        })

        # 2. 历史消息（从 AIFriendMemory 获取，转为 dict 格式）
        history = self.memory.get_messages()
        for msg in history:
            if hasattr(msg, 'content') and msg.content:
                role = "user" if msg.type == "human" else "assistant"
                messages.append({
                    "role": role,
                    "content": msg.content
                })

        # 3. 当前用户输入
        messages.append({
            "role": "user",
            "content": user_input
        })

        return messages

    async def chat(
        self,
        user_input: str,
        stream: bool = True
    ) -> AsyncGenerator[ChatResponse, None]:
        """ReAct 推理循环"""
        logger.info(f"[Pure] 处理用户输入: {user_input[:50]}...")
        messages = self._build_messages(user_input)
        full_content = ""
        model = self._get_litellm_model()

        try:
            for step in range(MAX_REACT_STEPS):
                logger.info(f"[Pure] ReAct 步骤 {step + 1}/{MAX_REACT_STEPS}")

                if stream:
                    async for response in self._stream_react_step(model, messages):
                        if isinstance(response, ChatResponse):
                            if response.content:
                                full_content += response.content
                            yield response
                else:
                    async for response in self._non_stream_react_step(model, messages):
                        if isinstance(response, ChatResponse):
                            if response.content:
                                full_content += response.content
                            yield response

                # 检查最后一条 assistant 消息是否包含 tool_calls
                # 如果没有，退出循环
                last_assistant = None
                for msg in reversed(messages):
                    if msg.get("role") == "assistant":
                        last_assistant = msg
                        break

                if not last_assistant or not last_assistant.get("tool_calls"):
                    break

            # 保存记忆
            if full_content:
                self.memory.add_user_message(user_input)
                self.memory.add_ai_message(full_content)
            else:
                # 尝试从 messages 中提取最终回复
                for msg in reversed(messages):
                    if msg.get("role") == "assistant" and msg.get("content"):
                        full_content = msg["content"]
                        break
                if full_content:
                    self.memory.add_user_message(user_input)
                    self.memory.add_ai_message(full_content)

        except Exception as e:
            logger.error(f"PurePythonAgent 执行错误: {e}", exc_info=True)
            yield ChatResponse(content=f"抱歉，处理时出现错误：{str(e)}")

    async def _stream_react_step(
        self,
        model: str,
        messages: List[dict],
    ) -> AsyncGenerator[ChatResponse, None]:
        """流式执行一次 ReAct 步骤"""
        kwargs = {
            "model": model,
            "messages": messages,
            "stream": True,
            "temperature": self.llm_config.temperature,
            "max_tokens": self.llm_config.max_tokens,
        }
        if self._tool_schemas:
            kwargs["tools"] = self._tool_schemas
        if self.llm_config.base_url:
            kwargs["api_base"] = self.llm_config.base_url

        response = await litellm.acompletion(**kwargs)

        full_content = ""
        tool_calls_buffer: Dict[int, dict] = {}

        async for chunk in response:
            if not chunk.choices:
                continue

            delta = chunk.choices[0].delta

            # 文本 token
            if delta.content:
                full_content += delta.content
                yield ChatResponse(content=delta.content)

            # 工具调用（流式拼接 delta）
            if delta.tool_calls:
                for tc in delta.tool_calls:
                    idx = tc.index if tc.index is not None else 0
                    if idx not in tool_calls_buffer:
                        tool_calls_buffer[idx] = {
                            "id": tc.id or f"call_{idx}",
                            "type": "function",
                            "function": {
                                "name": "",
                                "arguments": ""
                            }
                        }
                    if tc.id:
                        tool_calls_buffer[idx]["id"] = tc.id
                    if tc.function:
                        if tc.function.name:
                            tool_calls_buffer[idx]["function"]["name"] += tc.function.name
                        if tc.function.arguments:
                            tool_calls_buffer[idx]["function"]["arguments"] += tc.function.arguments

        # 构建 assistant 消息追加到 messages
        assistant_msg = {"role": "assistant", "content": full_content or None}
        if tool_calls_buffer:
            assistant_msg["tool_calls"] = list(tool_calls_buffer.values())
        messages.append(assistant_msg)

        # 如果有工具调用，执行并追加结果
        if tool_calls_buffer:
            for tc in tool_calls_buffer.values():
                tool_name = tc["function"]["name"]
                tool_args_str = tc["function"]["arguments"]

                yield ChatResponse(
                    content="",
                    debug_type="tool_call",
                    debug_title=f"调用工具: {tool_name}",
                    debug_content=f"```json\n{tool_args_str}\n```"
                )

                # 执行工具
                tool_result = await execute_tool_call(tc, self._tool_map)

                logger.info(f"[Pure] 工具 {tool_name} 执行完成")

                output_str = str(tool_result)
                if len(output_str) > 500:
                    output_str = output_str[:500] + "..."

                yield ChatResponse(
                    content="",
                    debug_type="tool_result",
                    debug_title=f"工具结果: {tool_name}",
                    debug_content=output_str
                )

                # 追加 tool 结果消息
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": str(tool_result)
                })

    async def _non_stream_react_step(
        self,
        model: str,
        messages: List[dict],
    ) -> AsyncGenerator[ChatResponse, None]:
        """非流式执行一次 ReAct 步骤"""
        kwargs = {
            "model": model,
            "messages": messages,
            "temperature": self.llm_config.temperature,
            "max_tokens": self.llm_config.max_tokens,
        }
        if self._tool_schemas:
            kwargs["tools"] = self._tool_schemas
        if self.llm_config.base_url:
            kwargs["api_base"] = self.llm_config.base_url

        response = await litellm.acompletion(**kwargs)
        message = response.choices[0].message

        content = message.content or ""
        assistant_msg = {"role": "assistant", "content": content or None}

        # 处理工具调用
        if message.tool_calls:
            tool_calls_list = []
            for tc in message.tool_calls:
                tc_dict = {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                }
                tool_calls_list.append(tc_dict)

                yield ChatResponse(
                    content="",
                    debug_type="tool_call",
                    debug_title=f"调用工具: {tc.function.name}",
                    debug_content=f"```json\n{tc.function.arguments}\n```"
                )

                # 执行工具
                tool_result = await execute_tool_call(tc_dict, self._tool_map)

                logger.info(f"[Pure] 工具 {tc.function.name} 执行完成")

                output_str = str(tool_result)
                if len(output_str) > 500:
                    output_str = output_str[:500] + "..."

                yield ChatResponse(
                    content="",
                    debug_type="tool_result",
                    debug_title=f"工具结果: {tc.function.name}",
                    debug_content=output_str
                )

                # 追加 tool 结果消息
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": str(tool_result)
                })

            assistant_msg["tool_calls"] = tool_calls_list
            messages.append(assistant_msg)
        else:
            messages.append(assistant_msg)
            yield ChatResponse(content=content)

    async def chat_with_history(
        self,
        user_input: str,
        history: List[Dict[str, str]],
        stream: bool = True
    ) -> AsyncGenerator[ChatResponse, None]:
        """带历史的对话"""
        self.memory.clear()

        for msg in history:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role == "user":
                self.memory.add_user_message(content)
            elif role == "assistant":
                self.memory.add_ai_message(content)

        async for response in self.chat(user_input, stream):
            yield response

    def update_tools(self, tools: List[StructuredTool]):
        """更新工具列表"""
        self.tools = tools
        self._tool_schemas = structured_tools_to_litellm(tools)
        self._tool_map = {t.name: t for t in tools}
        logger.info(f"[Pure] 工具已更新，数量: {len(self.tools)}")

    def update_llm(self, llm: BaseChatModel):
        """更新 LLM（Pure 模式下忽略 LangChain LLM，使用 litellm）"""
        logger.info("[Pure] update_llm 被调用，但 PurePythonAgent 使用 litellm 管理模型")

    def update_llm_config(self, llm_config: LLMProviderConfig):
        """更新 LLM 配置（Pure 模式专用）"""
        self.llm_config = llm_config
        self._setup_litellm()
        logger.info(f"[Pure] LLM 配置已更新: {llm_config.provider}/{llm_config.model}")
