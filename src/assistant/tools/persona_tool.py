# Persona Edit Tool
from typing import Dict, Any, Optional

from ...utils import get_character_manager, get_logger

logger = get_logger()


async def edit_persona(
    action: str,
    field: Optional[str] = None,
    value: Optional[str] = None,
    content: Optional[str] = None,
    key: Optional[str] = None,
    confirm: bool = False
) -> Dict[str, Any]:
    """编辑角色设定"""
    manager = get_character_manager()
    persona = manager.persona

    # 敏感字段需要确认
    sensitive_fields = ["name", "relationship", "background"]
    needs_confirm = action == "set_field" and field in sensitive_fields

    if needs_confirm and not confirm:
        return {
            "status": "needs_confirm",
            "message": f"这个修改比较重要，请先询问用户确认：将 {field} 改为 {value}"
        }

    # 执行修改
    try:
        if action == "set_name" and value:
            persona.name = value
        elif action == "set_field" and field:
            if hasattr(persona, field):
                setattr(persona, field, value)
        elif action == "add_memory" and content:
            manager.add_memory(content)
        elif action == "add_fact" and key and value:
            manager.set_fact(key, value)
        elif action == "remove_memory" and content:
            persona.memories = [
                m for m in persona.memories
                if content not in m.get("content", "")
            ]
        elif action == "remove_fact" and key:
            manager.remove_fact(key)

        manager.save()
        return {
            "status": "success",
            "message": "设定已更新"
        }
    except Exception as e:
        logger.error(f"修改设定失败: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


# 工具定义
PERSONA_TOOL = {
    "type": "function",
    "function": {
        "name": "edit_persona",
        "description": "修改角色设定、记忆、学到的信息。重要修改前先询问用户确认。",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["set_name", "set_field", "add_memory", "add_fact", "remove_memory", "remove_fact"],
                    "description": "操作类型"
                },
                "field": {
                    "type": "string",
                    "description": "字段名 (set_field 时使用): name, gender, age, personality, speech_style, first_person, second_person, user_nickname, relationship, background"
                },
                "value": {
                    "type": "string",
                    "description": "字段值"
                },
                "content": {
                    "type": "string",
                    "description": "记忆内容 (add_memory 时使用)"
                },
                "key": {
                    "type": "string",
                    "description": "事实键名 (add_fact/remove_fact 时使用)"
                },
                "confirm": {
                    "type": "boolean",
                    "default": False,
                    "description": "是否已经过用户确认"
                }
            },
            "required": ["action"]
        }
    }
}
