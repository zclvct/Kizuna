# System Tool
import psutil
from typing import Dict, Any


async def get_system_info() -> Dict[str, Any]:
    """获取系统信息"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        return {
            "cpu_percent": cpu_percent,
            "memory_total_gb": round(memory.total / (1024 ** 3), 2),
            "memory_used_gb": round(memory.used / (1024 ** 3), 2),
            "memory_percent": memory.percent,
            "disk_total_gb": round(disk.total / (1024 ** 3), 2),
            "disk_used_gb": round(disk.used / (1024 ** 3), 2),
            "disk_percent": disk.percent,
            "success": True
        }
    except Exception as e:
        return {
            "error": str(e),
            "success": False
        }


# 工具定义
SYSTEM_TOOL = {
    "type": "function",
    "function": {
        "name": "get_system_info",
        "description": "获取 CPU、内存、磁盘使用情况",
        "parameters": {"type": "object", "properties": {}, "required": []}
    }
}
