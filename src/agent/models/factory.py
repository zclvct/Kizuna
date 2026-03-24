# LangChain Chat Model Factory
from typing import Optional

from langchain_core.language_models.chat_models import BaseChatModel

from .config import LLMConfig, LLMProviderConfig
from utils import get_logger

logger = get_logger()

# 全局配置实例
_llm_config: Optional[LLMConfig] = None


def get_llm_config() -> LLMConfig:
    """获取全局 LLM 配置"""
    global _llm_config
    if _llm_config is None:
        from utils import get_config
        config = get_config()
        # 从旧配置转换
        config_data = {
            "llm": {
                "provider": config.llm.provider,
                "model": config.llm.model,
                "api_key": config.llm.api_key,
                "base_url": config.llm.base_url,
            },
            "llm_providers": config.llm_providers,
        }
        _llm_config = LLMConfig.from_legacy_config(config_data)
    return _llm_config


def create_chat_model(config: LLMProviderConfig) -> BaseChatModel:
    """根据配置创建 LangChain ChatModel
    
    Args:
        config: LLM 提供商配置
        
    Returns:
        LangChain BaseChatModel 实例
        
    Raises:
        ValueError: 不支持的提供商类型
    """
    logger.info(f"创建 ChatModel: provider={config.provider}, model={config.model}")
    
    if config.provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=config.model,
            api_key=config.api_key,
            base_url=config.base_url,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        )
    
    elif config.provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(
            model=config.model,
            base_url=config.base_url or "http://localhost:11434",
            temperature=config.temperature,
            num_predict=config.max_tokens,
        )
    
    elif config.provider == "anthropic":
        from langchain_openai import ChatOpenAI
        # Anthropic 通过 OpenAI 兼容 API 调用
        return ChatOpenAI(
            model=config.model,
            api_key=config.api_key,
            base_url=config.base_url or "https://api.anthropic.com/v1",
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        )
    
    elif config.provider == "deepseek":
        from langchain_openai import ChatOpenAI
        # DeepSeek 使用 OpenAI 兼容 API
        return ChatOpenAI(
            model=config.model,
            api_key=config.api_key,
            base_url=config.base_url or "https://api.deepseek.com/v1",
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        )
    
    else:
        # 默认尝试 OpenAI 兼容模式
        logger.warning(f"未知提供商类型 {config.provider}，尝试 OpenAI 兼容模式")
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=config.model,
            api_key=config.api_key,
            base_url=config.base_url,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        )


def get_default_chat_model() -> BaseChatModel:
    """获取默认的 ChatModel 实例
    
    使用全局配置中的默认提供商创建模型
    
    Returns:
        BaseChatModel 实例
    """
    config = get_llm_config()
    provider_config = config.get_provider_config()
    return create_chat_model(provider_config)
