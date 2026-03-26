# Mood Tool - 心情表情包工具
import json
import uuid
import shutil
from typing import Optional, Dict, Any, List
from pathlib import Path
from pydantic import BaseModel, Field

from utils import get_logger
from utils.constants import DATA_DIR, EMOJIS_DIR, resolve_path, get_relative_path

logger = get_logger()

# 心情数据文件路径 - 使用用户数据目录
MOODS_FILE = DATA_DIR / "moods.json"
EMOJI_DIR = EMOJIS_DIR

# 表情类型：心情类型 和 动作类型
MOOD_TYPES = {
    # 心情类型
    "happy": "开心",
    "sad": "难过",
    "angry": "生气",
    "excited": "兴奋",
    "shy": "害羞",
    "thinking": "思考",
    "surprised": "惊讶",
    "love": "喜欢",
    "confused": "困惑",
    "sleepy": "困倦",
    # 动作类型
    "greeting": "打招呼",
    "cute": "撒娇",
    "attack": "打人",
    "hug": "拥抱",
    "kiss": "亲亲",
    "cry": "哭泣",
    "laugh": "大笑",
    "doubt": "质疑",
    "encourage": "鼓励",
    "celebrate": "庆祝",
}

# 类型分类
CATEGORY_MOOD = "mood"  # 心情类型
CATEGORY_ACTION = "action"  # 动作类型


class MoodEntry(BaseModel):
    """心情/动作表情包条目"""
    id: str = Field(..., description="唯一ID")
    mood: str = Field(..., description="心情/动作类型")
    category: str = Field(CATEGORY_MOOD, description="类型分类: mood(心情) 或 action(动作)")
    file_path: str = Field(..., description="表情包文件路径")
    description: str = Field("", description="表情包描述")
    duration: int = Field(3000, description="显示持续时间(毫秒)")


class MoodsConfig(BaseModel):
    """心情配置"""
    moods: List[MoodEntry] = Field(default_factory=list)


def _ensure_emoji_dir():
    """确保表情包目录存在"""
    EMOJI_DIR.mkdir(parents=True, exist_ok=True)


def _load_moods() -> MoodsConfig:
    """加载心情配置"""
    if MOODS_FILE.exists():
        try:
            data = json.loads(MOODS_FILE.read_text(encoding="utf-8"))
            config = MoodsConfig(**data)
            logger.debug(f"加载心情配置成功: {len(config.moods)} 个条目")
            return config
        except Exception as e:
            logger.error(f"加载心情配置失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
    return MoodsConfig()


def _save_moods(config: MoodsConfig):
    """保存心情配置"""
    try:
        MOODS_FILE.parent.mkdir(parents=True, exist_ok=True)
        MOODS_FILE.write_text(
            config.model_dump_json(indent=2),
            encoding="utf-8"
        )
    except Exception as e:
        logger.error(f"保存心情配置失败: {e}")


def get_mood_by_type(mood: str) -> Optional[MoodEntry]:
    """根据心情/动作类型获取随机表情包"""
    config = _load_moods()
    import random
    matching = [m for m in config.moods if m.mood == mood]
    
    logger.debug(f"查找表情包 {mood}, 共 {len(config.moods)} 个配置, 匹配 {len(matching)} 个")
    
    if matching:
        chosen = random.choice(matching)
        logger.info(f"选中表情包: {chosen.mood} -> {chosen.file_path}")
        return chosen
    
    logger.warning(f"未找到类型 {mood} 的表情包，已配置类型: {[m.mood for m in config.moods]}")
    return None


def get_all_moods() -> List[MoodEntry]:
    """获取所有心情/动作配置"""
    config = _load_moods()
    return config.moods


def get_available_types() -> Dict[str, List[str]]:
    """获取已配置的表情类型
    
    Returns:
        {"mood": ["happy", "sad", ...], "action": ["greeting", "cute", ...]}
    """
    config = _load_moods()
    mood_types = set()
    action_types = set()
    
    for entry in config.moods:
        if entry.category == CATEGORY_ACTION:
            action_types.add(entry.mood)
        else:
            mood_types.add(entry.mood)
    
    return {
        CATEGORY_MOOD: sorted(list(mood_types)),
        CATEGORY_ACTION: sorted(list(action_types))
    }


def get_all_available_types() -> List[str]:
    """获取所有已配置的表情类型（扁平化列表）
    
    用于动态生成工具参数的 enum
    """
    types_dict = get_available_types()
    return types_dict[CATEGORY_MOOD] + types_dict[CATEGORY_ACTION]


def add_mood(
    mood: str, 
    source_file: str, 
    category: str = CATEGORY_MOOD,
    description: str = "", 
    duration: int = 3000
) -> MoodEntry:
    """添加心情/动作表情包
    
    Args:
        mood: 心情/动作类型
        source_file: 源文件路径
        category: 类型分类 (mood/action)
        description: 描述
        duration: 显示时长(毫秒)
    
    Returns:
        MoodEntry: 创建的心情条目
    """
    _ensure_emoji_dir()
    
    # 复制文件到 emoji 目录
    source_path = Path(source_file)
    if not source_path.exists():
        raise FileNotFoundError(f"文件不存在: {source_file}")
    
    # 生成目标文件名
    ext = source_path.suffix
    new_filename = f"{uuid.uuid4().hex[:8]}_{mood}{ext}"
    dest_path = EMOJI_DIR / new_filename
    
    shutil.copy2(source_path, dest_path)
    
    # 创建配置条目
    config = _load_moods()
    entry = MoodEntry(
        id=uuid.uuid4().hex[:8],
        mood=mood,
        category=category,
        file_path=str(dest_path.resolve()),
        description=description,
        duration=duration
    )
    
    config.moods.append(entry)
    _save_moods(config)
    logger.info(f"添加{category}表情包: {mood} -> {entry.file_path}")
    return entry


def remove_mood(mood_id: str) -> bool:
    """删除心情表情包"""
    config = _load_moods()
    
    for i, m in enumerate(config.moods):
        if m.id == mood_id:
            # 删除文件 - 使用 resolve_path 解析路径
            file_path = resolve_path(m.file_path)
            if file_path.exists():
                file_path.unlink()
            # 从配置中移除
            config.moods.pop(i)
            _save_moods(config)
            logger.info(f"删除心情表情包: {mood_id}")
            return True
    
    return False


# ============ 工具执行函数 ============

from PySide6.QtCore import QObject, Signal

# 全局信号发射器，用于跨线程触发表情包
class EmojiSignalEmitter(QObject):
    """表情包信号发射器"""
    emoji_triggered = Signal(str)  # 参数: mood

# 全局实例
_emoji_emitter = EmojiSignalEmitter()
_emoji_callback = None


def set_emoji_callback(callback):
    """设置表情包显示回调"""
    global _emoji_callback
    _emoji_callback = callback
    # 连接信号到回调
    _emoji_emitter.emoji_triggered.connect(callback)
    logger.info(f"表情包回调已设置并连接信号: {callback}")


def trigger_emoji(mood: str):
    """触发表情包显示（线程安全）"""
    import threading
    from PySide6.QtWidgets import QApplication
    
    logger.info(f"trigger_emoji 被调用: {mood}, 当前线程: {threading.current_thread().name}")
    
    if _emoji_callback is None:
        logger.warning("表情包回调未设置，请检查 MainWindow 初始化")
        return
    
    app = QApplication.instance()
    if not app:
        logger.error("QApplication 不存在")
        return
    
    # 使用信号发射，Qt 会自动处理线程安全
    logger.info(f"发射 emoji_triggered 信号: {mood}")
    _emoji_emitter.emoji_triggered.emit(mood)
    logger.info(f"信号已发射: {mood}")


async def show_mood_emoji(mood: str) -> Dict[str, Any]:
    """显示心情表情包
    
    Args:
        mood: 心情类型，如 happy, sad, angry, excited, shy, thinking, surprised
    
    Returns:
        执行结果
    """
    logger.info(f"显示心情表情包: {mood}")
    
    # 获取匹配的表情包
    entry = get_mood_by_type(mood)
    
    if not entry:
        # 没有配置的表情包，使用默认动作
        logger.warning(f"未找到心情 {mood} 的表情包")
        return {
            "status": "no_emoji",
            "mood": mood,
            "message": f"未配置 {mood} 心情的表情包"
        }
    
    # 触发表情包显示（线程安全）
    trigger_emoji(mood)
    
    return {
        "status": "success",
        "mood": mood,
        "emoji_path": entry.file_path,
        "duration": entry.duration,
        "description": entry.description
    }


# ============ 工具定义 ============

def get_mood_tool_definition() -> Dict[str, Any]:
    """获取心情表情包工具定义（动态生成enum）
    
    根据已配置的表情包动态生成参数枚举，防止调用未配置的类型
    """
    available_types = get_all_available_types()
    
    # 如果没有配置任何表情包，提供一个默认列表避免空enum
    if not available_types:
        available_types = ["happy"]
        logger.warning("未配置任何表情包，使用默认类型 [happy]")
    
    return {
        "type": "function",
        "function": {
            "name": "show_mood_emoji",
            "description": "显示心情或动作表情包气泡。在 Live2D 模型旁弹出表情包图片/GIF。支持心情类型（如开心、难过）和动作类型（如打招呼、撒娇）。在回复文字前调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "mood": {
                        "type": "string",
                        "enum": available_types,
                        "description": f"心情或动作类型。可用: {', '.join(available_types)}"
                    }
                },
                "required": ["mood"]
            }
        }
    }


# 保持向后兼容
MOOD_TOOL = get_mood_tool_definition()
