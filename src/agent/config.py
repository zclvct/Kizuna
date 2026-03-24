# Agent Configuration - 统一配置管理
from typing import Optional, List
from pathlib import Path
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

from agent.models.config import LLMConfig
from utils import get_logger, get_config

logger = get_logger()


class ToolConfigItem(BaseModel):
    """工具配置项"""
    id: str
    name: str
    description: str = ""
    enabled: bool = True


class AppConfig(BaseModel):
    """应用配置（整合所有配置）"""
    llm: LLMConfig
    tools: List[ToolConfigItem] = Field(default_factory=list)
    
    # Live2D 配置
    live2d_model_path: str = "assets/live2d/biaoqiang"
    live2d_scale: float = 1.0
    live2d_default_motion: str = "idle_01"
    
    # 动作配置
    enable_mood_motion: bool = True
    enable_idle_motion: bool = True
    idle_interval_seconds: int = 30
    
    # 通用配置
    auto_start: bool = False
    always_on_top: bool = True
    sound_enabled: bool = True
    log_level: str = "INFO"
    
    # 天气配置
    default_city: str = "北京"
    
    @classmethod
    def load(cls) -> "AppConfig":
        """从现有配置加载"""
        from utils import get_config, get_tools_config
        
        config = get_config()
        tools_config = get_tools_config()
        
        # 构建 LLM 配置
        config_data = {
            "llm": {
                "provider": config.llm.provider,
                "model": config.llm.model,
                "api_key": config.llm.api_key,
                "base_url": config.llm.base_url,
            },
            "llm_providers": config.llm_providers,
        }
        llm_config = LLMConfig.from_legacy_config(config_data)
        
        # 构建工具配置
        tools = [
            ToolConfigItem(
                id=tool.id,
                name=tool.name,
                description=tool.description,
                enabled=tool.enabled,
            )
            for tool in tools_config.get_all_tools()
        ]
        
        return cls(
            llm=llm_config,
            tools=tools,
            live2d_model_path=config.live2d.model_path,
            live2d_scale=config.live2d.scale,
            live2d_default_motion=config.live2d.default_motion,
            enable_mood_motion=config.motion.enable_mood_motion,
            enable_idle_motion=config.motion.enable_idle_motion,
            idle_interval_seconds=config.motion.idle_interval_seconds,
            auto_start=config.general.auto_start,
            always_on_top=config.general.always_on_top,
            sound_enabled=config.general.sound_enabled,
            log_level=config.general.log_level,
            default_city=config.weather.default_city,
        )
    
    def is_tool_enabled(self, tool_id: str) -> bool:
        """检查工具是否启用"""
        for tool in self.tools:
            if tool.id == tool_id:
                return tool.enabled
        return False
    
    def get_enabled_tool_ids(self) -> List[str]:
        """获取所有启用的工具 ID"""
        return [tool.id for tool in self.tools if tool.enabled]


# 全局配置实例
_app_config: Optional[AppConfig] = None


def get_app_config() -> AppConfig:
    """获取全局应用配置"""
    global _app_config
    if _app_config is None:
        _app_config = AppConfig.load()
        logger.info("应用配置已加载")
    return _app_config
