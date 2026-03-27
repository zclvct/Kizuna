# Motion Callback Management
from typing import Callable, Optional

from PySide6.QtCore import QObject, Signal, Qt

from utils.logger import get_logger

logger = get_logger()


class MotionSignalEmitter(QObject):
    """动作信号发射器"""
    motion_triggered = Signal(dict)


_motion_emitter = MotionSignalEmitter()
_motion_callback: Optional[Callable] = None
_motion_slot = None


def set_motion_callback(callback: Callable):
    """设置全局动作回调（线程安全）"""
    global _motion_callback, _motion_slot

    if _motion_slot is not None:
        try:
            _motion_emitter.motion_triggered.disconnect(_motion_slot)
        except Exception:
            pass

    _motion_callback = callback

    def _dispatch(payload: dict):
        try:
            callback(
                mood=payload.get("mood"),
                intent=payload.get("intent"),
                motion_id=payload.get("motion_id"),
                new_mood=payload.get("new_mood")
            )
        except Exception as e:
            logger.error(f"动作回调执行失败: {e}", exc_info=True)

    _motion_slot = _dispatch
    _motion_emitter.motion_triggered.connect(_motion_slot, Qt.ConnectionType.QueuedConnection)


def get_motion_callback() -> Optional[Callable]:
    """获取全局动作回调"""
    return _motion_callback


def trigger_motion(mood: str = None, intent: str = None, motion_id: str = None, new_mood: str = None):
    """触发动作（从工具调用，线程安全）"""
    global _motion_callback
    if not _motion_callback:
        logger.warning(
            f"[Motion Callback] No callback set. Motion: mood={mood}, intent={intent}, motion_id={motion_id}, new_mood={new_mood}"
        )
        return

    payload = {
        "mood": mood,
        "intent": intent,
        "motion_id": motion_id,
        "new_mood": new_mood,
    }

    try:
        _motion_emitter.motion_triggered.emit(payload)
    except Exception as e:
        logger.error(f"发射动作信号失败: {e}", exc_info=True)
        try:
            _motion_callback(**payload)
        except Exception as e2:
            logger.error(f"动作回调兜底执行失败: {e2}", exc_info=True)
