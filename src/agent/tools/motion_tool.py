# Motion Tool - Live2D 动作控制工具
from typing import List

from utils import get_logger, trigger_motion

logger = get_logger()


def get_available_motions() -> List[str]:
    """获取所有可用的动作 ID 列表
    
    动作 ID 从 Live2D 模型的 .model3.json 文件动态读取
    """
    from live2d_renderer.motion_controller import MotionController
    motion_controller = MotionController()
    motions = motion_controller.get_available_motions()
    
    if not motions:
        logger.warning("无法从模型读取动作列表，使用默认动作 [idle]")
        return ["idle"]
    
    return motions


async def play_motion(motion_id: str) -> dict:
    """播放 Live2D 动作
    
    Args:
        motion_id: 动作 ID，从模型的动作映射表中选择
    
    Returns:
        执行结果
    """
    logger.info(f"播放 Live2D 动作: {motion_id}")
    
    # 获取可用动作列表
    available_motions = get_available_motions()
    
    # 验证动作 ID 是否有效
    if motion_id not in available_motions:
        logger.warning(f"动作 ID '{motion_id}' 不在可用列表中，可用: {available_motions}")
    
    # 调用全局动作回调
    try:
        trigger_motion(motion_id=motion_id)
    except Exception as e:
        logger.error(f"触发动作失败: {e}")
        return {
            "status": "error",
            "motion_id": motion_id,
            "message": f"触发动作失败: {e}"
        }
    
    return {
        "status": "success",
        "motion_id": motion_id,
        "message": f"已播放动作: {motion_id}"
    }


# 工具定义（动态生成）
def get_motion_tool_definition() -> dict:
    """获取动作工具定义（动态生成 enum）"""
    available_motions = get_available_motions()
    return {
        "type": "function",
        "function": {
            "name": "play_motion",
            "description": "播放 Live2D 模型动作。必须直接指定动作 ID，用于控制模型的肢体动作和表情动画。动作 ID 从模型配置文件动态读取。在回复文字前调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "motion_id": {
                        "type": "string",
                        "enum": available_motions,
                        "description": f"动作 ID。可用: {', '.join(available_motions)}"
                    }
                },
                "required": ["motion_id"]
            }
        }
    }


# 保持向后兼容
MOTION_TOOL = get_motion_tool_definition()
