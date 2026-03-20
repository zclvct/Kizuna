# Time Tool
from datetime import datetime
from typing import Dict, Any


async def get_current_time(format: str = "%Y-%m-%d %H:%M:%S") -> Dict[str, Any]:
    """获取当前时间"""
    now = datetime.now()
    weekday_map = [
        "星期一", "星期二", "星期三",
        "星期四", "星期五", "星期六", "星期日"
    ]
    return {
        "time": now.strftime(format),
        "hour": now.hour,
        "minute": now.minute,
        "second": now.second,
        "weekday": weekday_map[now.weekday()],
        "date": now.strftime("%Y-%m-%d"),
        "year": now.year,
        "month": now.month,
        "day": now.day
    }


# 工具定义
TIME_TOOL = {
    "type": "function",
    "function": {
        "name": "get_current_time",
        "description": "获取当前时间、日期、星期几",
        "parameters": {
            "type": "object",
            "properties": {
                "format": {
                    "type": "string",
                    "description": "时间格式，默认 %Y-%m-%d %H:%M:%S"
                }
            },
            "required": []
        }
    }
}
