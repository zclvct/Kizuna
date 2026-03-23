# Persona Edit Tool
from typing import Dict, Any, Optional

from utils import get_character_manager, get_logger

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

    # 第一次启动时，不需要确认
    is_first_run = persona.is_first_run()

    # 敏感字段需要确认（第一次启动除外）
    sensitive_fields = ["name", "relationship", "background"]
    needs_confirm = action == "set_field" and field in sensitive_fields

    if needs_confirm and not confirm and not is_first_run:
        return {
            "status": "needs_confirm",
            "message": f"这个修改比较重要，请先询问用户确认：将 {field} 改为 {value}"
        }

    # 执行修改
    try:
        if action == "set_name" and value:
            persona.name = value
            logger.info(f"角色名字设置为: {value}")

            # 第一次设置名字时，添加一条记忆
            if is_first_run:
                manager.add_memory(f"用户给我起了名字叫{value}")

        elif action == "set_field" and field:
            if hasattr(persona, field):
                setattr(persona, field, value)
                logger.info(f"角色字段 {field} 设置为: {value}")

                # 第一次设置关系时，添加一条记忆
                if is_first_run and field == "relationship":
                    manager.add_memory(f"用户希望我和他的关系是：{value}")

        elif action == "add_memory" and content:
            manager.add_memory(content)
            logger.info(f"添加记忆: {content}")

        elif action == "add_fact" and key and value:
            manager.set_fact(key, value)
            logger.info(f"添加事实: {key} = {value}")

        elif action == "remove_memory" and content:
            persona.memories = [
                m for m in persona.memories
                if content not in m.get("content", "")
            ]
            logger.info(f"删除记忆: {content}")

        elif action == "remove_fact" and key:
            manager.remove_fact(key)
            logger.info(f"删除事实: {key}")

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
        "description": "修改角色设定、记忆、学到的信息。第一次启动时用于保存用户给的名字、关系等信息。重要修改前先询问用户确认。",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["set_name", "set_field", "add_memory", "add_fact", "remove_memory", "remove_fact"],
                    "description": "操作类型：set_name(设置名字), set_field(设置字段), add_memory(添加记忆), add_fact(添加事实), remove_memory(删除记忆), remove_fact(删除事实)"
                },
                "field": {
                    "type": "string",
                    "description": "字段名 (set_field 时使用): name(名字), gender(性别), age(年龄), personality(性格), speech_style(说话风格), first_person(自称), second_person(对用户称呼), user_nickname(用户昵称), relationship(关系), background(背景)"
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
                    "description": "事实键名 (add_fact/remove_fact 时使用)，如'用户喜好'、'用户作息'等"
                },
                "confirm": {
                    "type": "boolean",
                    "default": False,
                    "description": "是否已经过用户确认（第一次启动时不需要确认）"
                }
            },
            "required": ["action"]
        }
    }
}
