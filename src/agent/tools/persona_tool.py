# Persona Edit Tool - AI 角色设定工具
from typing import Dict, Any, Optional

from utils import get_character_manager, get_logger
from agent.memory import get_langchain_memory

logger = get_logger()


async def edit_persona(
    action: str,
    field: Optional[str] = None,
    value: Optional[str] = None,
    confirm: bool = False
) -> Dict[str, Any]:
    """编辑 AI 角色设定
    
    此工具专门用于设置 AI 的角色属性，包括名字、性格、说话风格等。
    用户相关的事实和记忆请使用 memory 工具（save_fact, save_memory）。
    """
    manager = get_character_manager()
    persona = manager.persona
    memory = get_langchain_memory()

    # 第一次启动时，不需要确认
    is_first_run = persona.is_first_run()

    # 敏感字段需要确认（第一次启动除外）
    sensitive_fields = ["name", "relationship"]
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

            # 第一次设置名字时，保存到长期记忆
            if is_first_run:
                memory.add_long_term_memory(
                    f"用户给我起了名字叫{value}",
                    importance=5
                )

        elif action == "set_field" and field:
            if hasattr(persona, field):
                setattr(persona, field, value)
                logger.info(f"角色字段 {field} 设置为: {value}")

                # 第一次设置关系时，保存到长期记忆
                if is_first_run and field == "relationship":
                    memory.add_long_term_memory(
                        f"用户希望我和他的关系是：{value}",
                        importance=4
                    )
                
                # 保存用户昵称为事实
                if field == "user_nickname" and value:
                    memory.save_fact("用户昵称", value)

        else:
            return {
                "status": "error",
                "message": f"无效的操作: {action}，或缺少必要参数"
            }

        manager.save()
        return {
            "status": "success",
            "message": f"已更新角色设定：{field or 'name'} = {value}"
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
        "description": """【AI角色设定】设置 AI 自己的角色属性。仅用于设置 AI 本身的设定，不存储用户信息！

可用操作：
- set_name: 设置 AI 的名字
- set_field: 设置 AI 的属性字段

可设置的字段（都是AI自己的属性）：
- name: AI的名字
- gender: AI的性别  
- age: AI的年龄
- personality: AI的性格特点
- speech_style: AI的说话风格
- first_person: AI的自称（如"我"、"本喵"）
- second_person: AI对用户的称呼（如"主人"、"你"）
- user_nickname: 用户在AI心中的昵称
- relationship: AI与用户的关系

【重要】用户的信息（姓名、爱好、喜欢吃什么等）请使用 save_fact 工具！""",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["set_name", "set_field"],
                    "description": "操作类型：set_name(设置名字), set_field(设置字段)"
                },
                "field": {
                    "type": "string",
                    "description": "字段名: name(AI名字), gender(AI性别), age(AI年龄), "
                                   "personality(AI性格特点), speech_style(AI说话风格), "
                                   "first_person(AI自称), second_person(AI对用户称呼), "
                                   "user_nickname(用户昵称), relationship(与用户关系)"
                },
                "value": {
                    "type": "string",
                    "description": "要设置的值"
                },
                "confirm": {
                    "type": "boolean",
                    "default": False,
                    "description": "是否已经过用户确认（重要字段修改时需要）"
                }
            },
            "required": ["action", "value"]
        }
    }
}
