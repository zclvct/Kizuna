# Clipboard Tool
import pyperclip
from typing import Dict, Any


async def get_clipboard() -> Dict[str, Any]:
    """获取剪贴板内容"""
    try:
        content = pyperclip.paste()
        return {
            "content": content,
            "success": True
        }
    except Exception as e:
        return {
            "error": str(e),
            "success": False
        }


async def set_clipboard(text: str) -> Dict[str, Any]:
    """设置剪贴板内容"""
    try:
        pyperclip.copy(text)
        return {
            "success": True
        }
    except Exception as e:
        return {
            "error": str(e),
            "success": False
        }


# 工具定义
CLIPBOARD_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_clipboard",
            "description": "获取当前剪贴板的内容",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_clipboard",
            "description": "设置剪贴板内容",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "要复制的文本"}
                },
                "required": ["text"]
            }
        }
    }
]
