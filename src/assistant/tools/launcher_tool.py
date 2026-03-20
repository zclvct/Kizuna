# Launcher Tool
import subprocess
import sys
import os
from typing import Dict, Any
from pathlib import Path

from ...utils import get_logger

logger = get_logger()


async def open_application(app_name: str) -> Dict[str, Any]:
    """打开应用或文件"""
    try:
        if sys.platform == "darwin":  # macOS
            subprocess.run(["open", app_name], check=True)
        elif sys.platform == "win32":  # Windows
            os.startfile(app_name)
        else:  # Linux
            subprocess.run(["xdg-open", app_name], check=True)

        return {
            "app_name": app_name,
            "success": True
        }
    except Exception as e:
        logger.error(f"打开应用失败: {e}")
        return {
            "app_name": app_name,
            "error": str(e),
            "success": False
        }


# 工具定义
LAUNCHER_TOOL = {
    "type": "function",
    "function": {
        "name": "open_application",
        "description": "打开应用程序或文件",
        "parameters": {
            "type": "object",
            "properties": {
                "app_name": {
                    "type": "string",
                    "description": "应用名称或文件路径"
                }
            },
            "required": ["app_name"]
        }
    }
}
