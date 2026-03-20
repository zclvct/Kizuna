# Motion Callback Management
from typing import Callable, Optional

_motion_callback: Optional[Callable] = None


def set_motion_callback(callback: Callable):
    """设置全局动作回调"""
    global _motion_callback
    _motion_callback = callback


def get_motion_callback() -> Optional[Callable]:
    """获取全局动作回调"""
    return _motion_callback


def trigger_motion(mood: str = None, intent: str = None, motion_id: str = None, new_mood: str = None):
    """触发动作（从工具调用）"""
    global _motion_callback
    if _motion_callback:
        _motion_callback(mood=mood, intent=intent, motion_id=motion_id, new_mood=new_mood)
    else:
        print(f"[Motion Callback] No callback set. Motion: mood={mood}, intent={intent}, motion_id={motion_id}, new_mood={new_mood}")
