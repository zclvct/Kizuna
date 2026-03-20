# Motion Tool
from typing import Optional

from ...utils import get_logger, trigger_motion

logger = get_logger()


async def play_motion(
    mood: Optional[str] = None,
    intent: Optional[str] = None,
    motion_id: Optional[str] = None,
    new_mood: Optional[str] = None
) -> dict:
    """播放 Live2D 动作"""
    logger.info(f"Play motion: mood={mood}, intent={intent}, motion_id={motion_id}, new_mood={new_mood}")

    # 调用全局动作回调
    try:
        trigger_motion(mood=mood, intent=intent, motion_id=motion_id, new_mood=new_mood)
    except Exception as e:
        logger.error(f"Failed to trigger motion: {e}")

    return {
        "status": "success",
        "mood": mood,
        "intent": intent,
        "motion_id": motion_id,
        "new_mood": new_mood
    }


# 工具定义
MOTION_TOOL = {
    "type": "function",
    "function": {
        "name": "play_motion",
        "description": "播放 Live2D 动作/表情来表达情绪。在回复文字前调用。",
        "parameters": {
            "type": "object",
            "properties": {
                "mood": {
                    "type": "string",
                    "enum": ["happy", "excited", "normal", "shy", "sad", "angry", "surprised", "thinking"],
                    "description": "心情类型，根据对话内容选择"
                },
                "intent": {
                    "type": "string",
                    "enum": ["greeting", "agree", "disagree", "thinking", "apologize", "thank", ""],
                    "description": "对话意图，可选，优先于 mood"
                },
                "motion_id": {
                    "type": "string",
                    "description": "直接指定动作 ID，可选，不指定则自动选择"
                },
                "new_mood": {
                    "type": "string",
                    "enum": ["happy", "excited", "normal", "shy", "sad", "angry", "surprised", "thinking"],
                    "description": "更新角色心情，可选"
                }
            },
            "required": []
        }
    }
}
