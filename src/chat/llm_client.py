# LLM Client
import sys
from pathlib import Path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from typing import List, Dict, Optional, Any, AsyncGenerator
from dataclasses import dataclass
import json

from litellm import acompletion

from utils import get_config, get_character_manager, get_logger

logger = get_logger()


@dataclass
class LLMConfig:
    """LLM 配置"""
    provider: str
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2000


class LLMClient:
    """LLM 客户端"""

    def __init__(self):
        config = get_config()
        self.config = LLMConfig(
            provider=config.llm.provider,
            model=config.llm.model,
            api_key=config.llm.api_key,
            base_url=config.llm.base_url,
        )
        self.character_manager = get_character_manager()

    def _get_litellm_model(self) -> str:
        """获取 LiteLLM 格式的模型名"""
        provider = self.config.provider
        model = self.config.model

        if provider == "openai":
            return f"openai/{model}"
        elif provider == "anthropic":
            return f"anthropic/{model}"
        elif provider == "ollama":
            return f"ollama/{model}"
        return model

    def _build_system_prompt(self) -> str:
        """构建 System Prompt"""
        persona = self.character_manager.persona
        state = self.character_manager.state

        base = persona.to_system_prompt()

        mood_info = f"\n\n你当前的心情是：{state.current_mood}"

        tool_instruction = """

你可以使用以下工具来帮助用户：
1. play_motion - 播放 Live2D 动作来表达情绪
2. edit_persona - 修改你的设定、记忆等（重要修改前先确认）

请在回复文字前先调用合适的工具。
"""

        return base + mood_info + tool_instruction

    def _get_common_params(self) -> Dict[str, Any]:
        """获取通用参数"""
        params = {
            "model": self._get_litellm_model(),
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }
        if self.config.api_key:
            params["api_key"] = self.config.api_key
        if self.config.base_url:
            params["api_base"] = self.config.base_url
        return params

    async def chat(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        stream: bool = False
    ) -> Any:
        """发送对话请求"""
        params = self._get_common_params()

        # 添加 system prompt
        full_messages = [
            {"role": "system", "content": self._build_system_prompt()}
        ] + messages

        params["messages"] = full_messages

        if tools:
            params["tools"] = tools

        logger.info(f"Calling LLM: {self.config.provider}/{self.config.model}")

        try:
            if stream:
                return await self._chat_stream(params)
            else:
                response = await acompletion(**params)
                return response
        except Exception as e:
            logger.error(f"LLM 调用失败: {e}")
            raise

    async def _chat_stream(self, params: Dict) -> AsyncGenerator[str, None]:
        """流式输出"""
        params["stream"] = True
        response = await acompletion(**params)

        async for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


# 全局实例
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """获取 LLM 客户端"""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
