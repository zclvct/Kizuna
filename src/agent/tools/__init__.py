# Assistant Tools
# 原有工具函数（保持兼容）
from .time_tool import get_current_time, TIME_TOOL
from .weather_tool import get_weather, WEATHER_TOOL
from .todo_tool import add_todo, list_todos, complete_todo, TODO_TOOLS, get_todo_manager
from .clipboard_tool import get_clipboard, set_clipboard, CLIPBOARD_TOOLS
from .system_tool import get_system_info, SYSTEM_TOOL
from .launcher_tool import open_application, LAUNCHER_TOOL
from .persona_tool import edit_persona, PERSONA_TOOL
from .motion_tool import play_motion, MOTION_TOOL, get_available_motions, get_motion_tool_definition
from .mood_tool import (
    show_mood_emoji, 
    MOOD_TOOL, 
    set_emoji_callback, 
    trigger_emoji,
    get_mood_tool_definition,
    get_all_available_types,
    get_available_types,
    MOOD_TYPES,
    CATEGORY_MOOD,
    CATEGORY_ACTION
)

# LangChain 工具支持
from .base import BaseToolArgs, LangChainTool, create_tool_from_function
from .langchain_tools import (
    create_time_tool,
    create_weather_tool,
    create_add_todo_tool,
    create_list_todos_tool,
    create_complete_todo_tool,
    create_get_clipboard_tool,
    create_set_clipboard_tool,
    create_system_info_tool,
    create_launcher_tool,
    create_persona_tool,
    create_motion_tool,
    create_mood_emoji_tool,
    get_all_tools,
    get_tools_by_ids,
)
from .registry import ToolRegistry, get_tool_registry

__all__ = [
    # 原有工具函数
    "get_current_time",
    "TIME_TOOL",
    "get_weather",
    "WEATHER_TOOL",
    "add_todo",
    "list_todos",
    "complete_todo",
    "TODO_TOOLS",
    "get_todo_manager",
    "get_clipboard",
    "set_clipboard",
    "CLIPBOARD_TOOLS",
    "get_system_info",
    "SYSTEM_TOOL",
    "open_application",
    "LAUNCHER_TOOL",
    "edit_persona",
    "PERSONA_TOOL",
    "play_motion",
    "MOTION_TOOL",
    "get_available_motions",
    "get_motion_tool_definition",
    "show_mood_emoji",
    "MOOD_TOOL",
    "set_emoji_callback",
    "trigger_emoji",
    "get_mood_tool_definition",
    "get_all_available_types",
    "get_available_types",
    "MOOD_TYPES",
    "CATEGORY_MOOD",
    "CATEGORY_ACTION",
    # LangChain 工具
    "BaseToolArgs",
    "LangChainTool",
    "create_tool_from_function",
    "create_time_tool",
    "create_weather_tool",
    "create_add_todo_tool",
    "create_list_todos_tool",
    "create_complete_todo_tool",
    "create_get_clipboard_tool",
    "create_set_clipboard_tool",
    "create_system_info_tool",
    "create_launcher_tool",
    "create_persona_tool",
    "create_motion_tool",
    "create_mood_emoji_tool",
    "get_all_tools",
    "get_tools_by_ids",
    "ToolRegistry",
    "get_tool_registry",
]
