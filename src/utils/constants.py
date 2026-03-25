# Constants
from pathlib import Path
from typing import Union

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent

# 数据目录
DATA_DIR = PROJECT_ROOT / "data"
ASSETS_DIR = PROJECT_ROOT / "assets"
LIVE2D_MODELS_DIR = ASSETS_DIR / "live2d"
IMAGES_DIR = ASSETS_DIR / "images"

# 数据文件
CONFIG_FILE = DATA_DIR / "config.json"
CHARACTER_FILE = DATA_DIR / "character.json"
TOOLS_FILE = DATA_DIR / "tools.json"
MOTIONS_FILE = DATA_DIR / "motions.json"
CONVERSATIONS_FILE = DATA_DIR / "conversations.json"
SCHEDULED_TASKS_FILE = DATA_DIR / "scheduled_tasks.json"
TODO_FILE = DATA_DIR / "todos.json"


def resolve_path(path: Union[str, Path]) -> Path:
    """解析路径，支持相对路径和绝对路径
    
    Args:
        path: 路径字符串或 Path 对象
        
    Returns:
        解析后的绝对路径
    """
    path = Path(path)
    
    # 如果已经是绝对路径且存在，直接返回
    if path.is_absolute():
        if path.exists():
            return path
        # 绝对路径但不存在，尝试从项目根目录查找
        # 这处理了文件夹改名后绝对路径失效的情况
    
    # 尝试相对于项目根目录解析
    abs_path = PROJECT_ROOT / path
    if abs_path.exists():
        return abs_path
    
    # 如果路径包含 assets 或 data，尝试提取相对部分
    path_str = str(path)
    for prefix in ["assets", "data"]:
        if prefix in path_str:
            # 提取 assets 或 data 之后的部分
            idx = path_str.find(prefix)
            relative_part = path_str[idx:]
            new_path = PROJECT_ROOT / relative_part
            if new_path.exists():
                return new_path
    
    # 都找不到，返回原始解析结果（让调用者处理不存在的情况）
    return abs_path


def get_relative_path(path: Union[str, Path]) -> str:
    """将绝对路径转换为相对路径（相对于项目根目录）
    
    Args:
        path: 绝对路径
        
    Returns:
        相对路径字符串
    """
    path = Path(path)
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        # 不在项目根目录下，返回原路径
        return str(path)

# 确保目录存在
for dir_path in [DATA_DIR, LIVE2D_MODELS_DIR, IMAGES_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# 默认配置
DEFAULT_LLM_PROVIDER = "openai"
DEFAULT_LLM_MODEL = "gpt-4"
DEFAULT_WEATHER_CITY = "北京"

# 心情列表
MOODS = [
    "happy",
    "excited",
    "normal",
    "shy",
    "sad",
    "angry",
    "surprised",
    "thinking"
]

# 意图列表
INTENTS = [
    "greeting",
    "agree",
    "disagree",
    "thinking",
    "apologize",
    "thank"
]

# 默认技能
DEFAULT_TOOLS = [
    {"id": "time", "name": "时间工具", "description": "查询时间、日期、星期", "enabled": True},
    {"id": "weather", "name": "天气工具", "description": "查询天气预报", "enabled": True},
    {"id": "todo", "name": "待办事项", "description": "管理待办任务", "enabled": True},
    {"id": "clipboard", "name": "剪贴板助手", "description": "操作剪贴板内容", "enabled": False},
    {"id": "system", "name": "系统信息", "description": "查看电脑状态", "enabled": False},
    {"id": "launcher", "name": "应用启动", "description": "打开应用和文件", "enabled": False},
    {"id": "scheduler", "name": "定时任务", "description": "创建定时提醒", "enabled": True},
    {"id": "persona_edit", "name": "角色设定编辑", "description": "学习和修改设定", "enabled": True},
    {"id": "motion_control", "name": "动作控制", "description": "控制 Live2D 动作和表情", "enabled": True}
]

# 默认动作配置
# 注意：实际可用动作从 Live2D 模型的 .model3.json 文件动态读取
# 此配置仅作为心情-动作映射的默认值参考
DEFAULT_MOTIONS_CONFIG = {
    "model_id": "default",
    "description": "Live2D 模型动作配置。动作 ID 从模型文件的 Motions 字段动态读取，无需手动配置 available_motions。",
    "mood_motions": {
        "happy": ["main_1", "main_2"],
        "excited": ["main_1", "mission_complete"],
        "normal": ["idle"],
        "shy": ["touch_head"],
        "sad": ["idle"],
        "angry": ["idle"],
        "surprised": ["touch_special"],
        "thinking": ["idle"]
    },
    "intent_motions": {
        "greeting": ["home", "login"],
        "agree": ["main_1"],
        "disagree": ["idle"],
        "thinking": ["idle"],
        "apologize": ["touch_body"],
        "thank": ["main_2"]
    },
    "idle_motions": ["idle"],
    "default_motion": "idle",
    "settings": {
        "enable_mood_motion": True,
        "enable_idle_motion": True,
        "enable_chat_motion": True,
        "idle_interval_seconds": 30
    }
}
