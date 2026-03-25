# Constants
import os
import sys
import shutil
from pathlib import Path
from typing import Union
import platform

# 项目根目录（代码所在位置，用于读取默认资源）
# 兼容 PyInstaller 打包环境
if getattr(sys, 'frozen', False):
    # PyInstaller 打包后的路径
    PROJECT_ROOT = Path(sys._MEIPASS)
else:
    # 正常开发环境
    PROJECT_ROOT = Path(__file__).parent.parent.parent


def get_user_data_dir() -> Path:
    """获取跨平台的用户数据目录
    
    macOS: ~/Kizuna
    Windows: %USERPROFILE%\\Kizuna
    Linux: ~/Kizuna
    
    Returns:
        用户数据目录路径
    """
    home = Path.home()
    app_name = "Kizuna"
    
    system = platform.system()
    if system == "Windows":
        # Windows: C:\\Users\\用户名\\Kizuna
        user_data = Path(os.environ.get("USERPROFILE", home)) / app_name
    else:
        # macOS/Linux: ~/Kizuna
        user_data = home / app_name
    
    return user_data


def _init_user_data_dir():
    """初始化用户数据目录，用户目录下没有对应文件夹时从项目目录复制"""
    user_data = get_user_data_dir()
    project_data = PROJECT_ROOT / "data"
    project_assets = PROJECT_ROOT / "assets"
    
    # 如果 data 目录不存在，从项目复制
    data_target = user_data / "data"
    if not data_target.exists() and project_data.exists():
        shutil.copytree(project_data, data_target)
    
    # 确保 assets 子目录存在
    (user_data / "assets").mkdir(parents=True, exist_ok=True)
    
    # 如果 live2d 目录不存在，从项目复制
    live2d_target = user_data / "assets" / "live2d"
    if not live2d_target.exists() and (project_assets / "live2d").exists():
        shutil.copytree(project_assets / "live2d", live2d_target)
    
    # 如果 images 目录不存在，从项目复制
    images_target = user_data / "assets" / "images"
    if not images_target.exists() and (project_assets / "images").exists():
        shutil.copytree(project_assets / "images", images_target)
    
    # 如果 emojis 目录不存在，从项目复制
    emojis_target = user_data / "assets" / "emojis"
    if not emojis_target.exists() and (project_assets / "emojis").exists():
        shutil.copytree(project_assets / "emojis", emojis_target)


# 初始化用户数据目录
_init_user_data_dir()

# 用户数据目录（配置、记忆等）
USER_DATA_DIR = get_user_data_dir()

# 数据目录 - 使用用户目录
DATA_DIR = USER_DATA_DIR / "data"
ASSETS_DIR = USER_DATA_DIR / "assets"
LIVE2D_MODELS_DIR = ASSETS_DIR / "live2d"
IMAGES_DIR = ASSETS_DIR / "images"
EMOJIS_DIR = ASSETS_DIR / "emojis"

# 项目内置资源目录（只读资源，如默认图标）
BUILTIN_ASSETS_DIR = PROJECT_ROOT / "assets"

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
    
    优先级：
    1. 如果是绝对路径且存在，直接返回
    2. 尝试从用户数据目录解析
    3. 尝试从项目目录解析（用于内置资源）
    
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
    
    # 尝试相对于用户数据目录解析
    user_path = USER_DATA_DIR / path
    if user_path.exists():
        return user_path
    
    # 尝试相对于项目根目录解析（用于内置资源）
    project_path = PROJECT_ROOT / path
    if project_path.exists():
        return project_path
    
    # 如果路径包含 assets 或 data，尝试提取相对部分
    path_str = str(path)
    for prefix in ["assets", "data"]:
        if prefix in path_str:
            idx = path_str.find(prefix)
            relative_part = path_str[idx:]
            
            # 先尝试用户目录
            user_path = USER_DATA_DIR / relative_part
            if user_path.exists():
                return user_path
            
            # 再尝试项目目录
            project_path = PROJECT_ROOT / relative_part
            if project_path.exists():
                return project_path
    
    # 默认返回用户数据目录下的路径（用于新建文件）
    return user_path


def get_relative_path(path: Union[str, Path]) -> str:
    """将绝对路径转换为相对路径（相对于用户数据目录）
    
    Args:
        path: 绝对路径
        
    Returns:
        相对路径字符串
    """
    path = Path(path)
    try:
        return str(path.relative_to(USER_DATA_DIR))
    except ValueError:
        try:
            # 如果不在用户目录，尝试相对于项目目录
            return str(path.relative_to(PROJECT_ROOT))
        except ValueError:
            # 都不在，返回原路径
            return str(path)

# 确保目录存在
for dir_path in [DATA_DIR, LIVE2D_MODELS_DIR, IMAGES_DIR, EMOJIS_DIR]:
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
