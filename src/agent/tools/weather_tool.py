# Weather Tool
import requests
from typing import Dict, Any, Optional
from utils import get_logger

logger = get_logger()


async def get_weather(city: str = "北京") -> Dict[str, Any]:
    """获取天气 (使用 wttr.in 免费 API)"""
    try:
        url = f"https://wttr.in/{city}?format=j1"
        response = requests.get(url, timeout=10)
        data = response.json()

        current = data.get("current_condition", [{}])[0]
        weather_desc = current.get("lang_zh", [{}])[0].get("value", "")
        temp = current.get("temp_C", "")
        feels_like = current.get("FeelsLikeC", "")
        humidity = current.get("humidity", "")
        wind = current.get("windspeedKmph", "")

        return {
            "city": city,
            "weather": weather_desc,
            "temperature": temp,
            "feels_like": feels_like,
            "humidity": humidity,
            "wind_speed": wind,
            "success": True
        }
    except Exception as e:
        logger.error(f"获取天气失败: {e}")
        return {
            "city": city,
            "error": str(e),
            "success": False
        }


# 工具定义
WEATHER_TOOL = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "查询指定城市的天气情况",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "城市名称，默认北京"
                }
            },
            "required": []
        }
    }
}
