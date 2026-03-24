# LLM Configuration for LangChain
from typing import Optional, Literal
from pydantic import BaseModel, Field


class LLMProviderConfig(BaseModel):
    """单个 LLM 提供商配置"""
    name: str = Field(..., description="配置名称")
    provider: Literal["openai", "ollama", "anthropic", "deepseek"] = Field(..., description="提供商类型")
    model: str = Field(..., description="模型名称")
    api_key: Optional[str] = Field(None, description="API Key")
    base_url: Optional[str] = Field(None, description="API 基础 URL")
    temperature: float = Field(0.7, ge=0, le=2, description="温度参数")
    max_tokens: int = Field(2000, ge=1000, le=256000, description="最大输出 tokens")
    
    class Config:
        extra = "allow"


class LLMConfig(BaseModel):
    """LLM 全局配置"""
    default_provider: str = Field("ollama", description="默认提供商配置名称")
    providers: dict[str, LLMProviderConfig] = Field(default_factory=dict, description="提供商配置映射")
    
    def get_provider_config(self, name: Optional[str] = None) -> LLMProviderConfig:
        """获取提供商配置
        
        Args:
            name: 提供商配置名称，为空则使用默认
            
        Returns:
            LLMProviderConfig 实例
            
        Raises:
            ValueError: 配置不存在时抛出
        """
        provider_name = name or self.default_provider
        if provider_name not in self.providers:
            raise ValueError(f"LLM 提供商配置不存在: {provider_name}")
        return self.providers[provider_name]
    
    @classmethod
    def from_legacy_config(cls, config_data: dict) -> "LLMConfig":
        """从旧配置格式创建
        
        Args:
            config_data: 旧配置数据，包含 llm 和 llm_providers 字段
            
        Returns:
            LLMConfig 实例
        """
        providers = {}
        
        # 从 llm_providers 加载
        if "llm_providers" in config_data:
            for p in config_data["llm_providers"].get("providers", []):
                name = p.get("name", "default")
                providers[name] = LLMProviderConfig(
                    name=name,
                    provider=p.get("provider", "ollama"),
                    model=p.get("model", ""),
                    api_key=p.get("api_key"),
                    base_url=p.get("base_url"),
                    temperature=p.get("temperature", 0.7),
                    max_tokens=p.get("max_tokens", 2000),
                )
        
        # 如果没有配置，使用主 llm 配置创建默认
        if not providers and "llm" in config_data:
            llm = config_data["llm"]
            providers["default"] = LLMProviderConfig(
                name="default",
                provider=llm.get("provider", "ollama"),
                model=llm.get("model", ""),
                api_key=llm.get("api_key"),
                base_url=llm.get("base_url"),
                temperature=llm.get("temperature", 0.7),
                max_tokens=llm.get("max_tokens", 2000),
            )
        
        default_index = config_data.get("llm_providers", {}).get("default_index", 0)
        default_name = list(providers.keys())[default_index] if providers else "default"
        
        return cls(default_provider=default_name, providers=providers)
