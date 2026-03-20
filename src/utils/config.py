# Configuration Management
import os
import json
from typing import Optional, Dict, Any
from pathlib import Path
from dataclasses import dataclass, asdict
from dotenv import load_dotenv

from .constants import (
    CONFIG_FILE,
    DEFAULT_LLM_PROVIDER,
    DEFAULT_LLM_MODEL,
    DEFAULT_WEATHER_CITY,
    PROJECT_ROOT
)
from .logger import get_logger

logger = get_logger()

# 加载环境变量
load_dotenv(PROJECT_ROOT / ".env")


@dataclass
class LLMConfig:
    """LLM 配置"""
    provider: str = DEFAULT_LLM_PROVIDER
    model: str = DEFAULT_LLM_MODEL
    api_key: Optional[str] = None
    base_url: Optional[str] = None


@dataclass
class Live2DConfig:
    """Live2D 配置"""
    model_path: str = "assets/live2d/default"
    scale: float = 1.0
    default_motion: str = "idle_01"


@dataclass
class WeatherConfig:
    """天气配置"""
    default_city: str = DEFAULT_WEATHER_CITY


@dataclass
class GeneralConfig:
    """通用配置"""
    auto_start: bool = False
    always_on_top: bool = True
    sound_enabled: bool = True
    log_level: str = "INFO"


@dataclass
class MotionSettings:
    """动作设置"""
    enable_mood_motion: bool = True
    enable_idle_motion: bool = True
    idle_interval_seconds: int = 30


class Config:
    """配置管理"""

    def __init__(self):
        self.llm = LLMConfig()
        self.live2d = Live2DConfig()
        self.weather = WeatherConfig()
        self.general = GeneralConfig()
        self.motion = MotionSettings()
        self._load_from_env()
        self._load_from_file()

    def _load_from_env(self):
        """从环境变量加载配置"""
        # LLM
        self.llm.provider = os.getenv("LLM_PROVIDER", self.llm.provider)
        self.llm.model = os.getenv("LLM_MODEL", self.llm.model)
        self.llm.api_key = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
        self.llm.base_url = os.getenv("OPENAI_BASE_URL") or os.getenv("OLLAMA_BASE_URL")

        # Weather
        self.weather.default_city = os.getenv("WEATHER_DEFAULT_CITY", self.weather.default_city)

        # Live2D
        live2d_path = os.getenv("LIVE2D_MODEL_PATH")
        if live2d_path:
            self.live2d.model_path = live2d_path

    def _load_from_file(self):
        """从配置文件加载"""
        if not CONFIG_FILE.exists():
            return

        try:
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))

            if "llm" in data:
                for key, value in data["llm"].items():
                    if hasattr(self.llm, key):
                        setattr(self.llm, key, value)

            if "live2d" in data:
                for key, value in data["live2d"].items():
                    if hasattr(self.live2d, key):
                        setattr(self.live2d, key, value)

            if "weather" in data:
                for key, value in data["weather"].items():
                    if hasattr(self.weather, key):
                        setattr(self.weather, key, value)

            if "general" in data:
                for key, value in data["general"].items():
                    if hasattr(self.general, key):
                        setattr(self.general, key, value)

            if "motion" in data:
                for key, value in data["motion"].items():
                    if hasattr(self.motion, key):
                        setattr(self.motion, key, value)

            logger.info("配置已从文件加载")
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")

    def save(self):
        """保存配置到文件"""
        data = {
            "llm": asdict(self.llm),
            "live2d": asdict(self.live2d),
            "weather": asdict(self.weather),
            "general": asdict(self.general),
            "motion": asdict(self.motion)
        }

        CONFIG_FILE.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        logger.info("配置已保存")


# 全局配置实例
_config_instance: Optional[Config] = None


def get_config() -> Config:
    """获取全局配置实例"""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance
