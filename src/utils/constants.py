# Constants
from pathlib import Path

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
SKILLS_FILE = DATA_DIR / "skills.json"
MOTIONS_FILE = DATA_DIR / "motions.json"
CONVERSATIONS_FILE = DATA_DIR / "conversations.json"
SCHEDULED_TASKS_FILE = DATA_DIR / "scheduled_tasks.json"
TODO_FILE = DATA_DIR / "todos.json"

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
DEFAULT_SKILLS = [
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
DEFAULT_MOTIONS_CONFIG = {
    "model_id": "default",
    "mood_motions": {
        "happy": ["happy_01", "happy_02"],
        "excited": ["excited_01"],
        "normal": ["idle_01", "idle_02"],
        "shy": ["shy_01"],
        "sad": ["sad_01"],
        "angry": ["angry_01"],
        "surprised": ["surprised_01"],
        "thinking": ["thinking_01"]
    },
    "intent_motions": {
        "greeting": ["wave", "smile"],
        "agree": ["nod", "smile"],
        "disagree": ["shake_head"],
        "thinking": ["thinking_01"],
        "apologize": ["apologize_01"],
        "thank": ["thank_01"]
    },
    "idle_motions": ["idle_01", "idle_02"],
    "default_motion": "idle_01",
    "settings": {
        "enable_mood_motion": True,
        "enable_idle_motion": True,
        "idle_interval_seconds": 30
    }
}
