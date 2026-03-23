# Tool Registry
import sys
from pathlib import Path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from typing import Dict, List, Any, Callable, Optional
from dataclasses import dataclass
import json

from assistant.tools import (
    get_current_time, TIME_TOOL,
    get_weather, WEATHER_TOOL,
    add_todo, list_todos, complete_todo, TODO_TOOLS,
    get_clipboard, set_clipboard, CLIPBOARD_TOOLS,
    get_system_info, SYSTEM_TOOL,
    open_application, LAUNCHER_TOOL,
    edit_persona, PERSONA_TOOL,
    play_motion, MOTION_TOOL,
)
from utils import get_logger, get_skills_manager

logger = get_logger()


@dataclass
class Tool:
    """工具定义"""
    name: str
    description: str
    parameters: Dict[str, Any]
    handler: Callable


class ToolRegistry:
    """工具注册表"""

    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        self._register_default_tools()

    def _register_default_tools(self):
        """注册默认工具"""
        # 时间工具
        self.register(Tool(
            name="get_current_time",
            description=TIME_TOOL["function"]["description"],
            parameters=TIME_TOOL["function"]["parameters"],
            handler=get_current_time
        ))

        # 天气工具
        self.register(Tool(
            name="get_weather",
            description=WEATHER_TOOL["function"]["description"],
            parameters=WEATHER_TOOL["function"]["parameters"],
            handler=get_weather
        ))

        # 待办工具
        for tool_def in TODO_TOOLS:
            self.register(Tool(
                name=tool_def["function"]["name"],
                description=tool_def["function"]["description"],
                parameters=tool_def["function"]["parameters"],
                handler=globals()[tool_def["function"]["name"]]
            ))

        # 剪贴板工具
        for tool_def in CLIPBOARD_TOOLS:
            self.register(Tool(
                name=tool_def["function"]["name"],
                description=tool_def["function"]["description"],
                parameters=tool_def["function"]["parameters"],
                handler=globals()[tool_def["function"]["name"]]
            ))

        # 系统工具
        self.register(Tool(
            name="get_system_info",
            description=SYSTEM_TOOL["function"]["description"],
            parameters=SYSTEM_TOOL["function"]["parameters"],
            handler=get_system_info
        ))

        # 启动工具
        self.register(Tool(
            name="open_application",
            description=LAUNCHER_TOOL["function"]["description"],
            parameters=LAUNCHER_TOOL["function"]["parameters"],
            handler=open_application
        ))

        # 角色设定工具
        self.register(Tool(
            name="edit_persona",
            description=PERSONA_TOOL["function"]["description"],
            parameters=PERSONA_TOOL["function"]["parameters"],
            handler=edit_persona
        ))

        # 动作工具
        self.register(Tool(
            name="play_motion",
            description=MOTION_TOOL["function"]["description"],
            parameters=MOTION_TOOL["function"]["parameters"],
            handler=play_motion
        ))

    def register(self, tool: Tool):
        """注册工具"""
        self._tools[tool.name] = tool
        logger.debug(f"Tool registered: {tool.name}")

    @property
    def tools(self) -> Dict[str, Tool]:
        """获取所有工具"""
        return self._tools

    def get_tool(self, name: str) -> Optional[Tool]:
        """获取工具"""
        return self._tools.get(name)

    def to_openai_tools(self) -> List[Dict]:
        """转换为 OpenAI tools 格式（仅返回启用的工具）"""
        skills_manager = get_skills_manager()
        enabled_tools = skills_manager.get_enabled_tools()

        all_tools = [
            TIME_TOOL,
            WEATHER_TOOL,
            *TODO_TOOLS,
            *CLIPBOARD_TOOLS,
            SYSTEM_TOOL,
            LAUNCHER_TOOL,
            PERSONA_TOOL,
            MOTION_TOOL
        ]

        # 过滤出启用的工具
        filtered_tools = []
        for tool_def in all_tools:
            tool_name = tool_def["function"]["name"]
            if tool_name in enabled_tools:
                filtered_tools.append(tool_def)
            else:
                logger.debug(f"Tool disabled by skill setting: {tool_name}")

        logger.info(f"返回 {len(filtered_tools)} 个启用的工具")
        return filtered_tools

    async def execute(self, name: str, arguments: Dict) -> Any:
        """执行工具"""
        tool = self._tools.get(name)
        if not tool:
            raise ValueError(f"Tool not found: {name}")

        logger.info(f"Executing tool: {name} with args: {arguments}")
        return await tool.handler(**arguments)


# 全局工具注册表
_tool_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """获取工具注册表"""
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = ToolRegistry()
    return _tool_registry
