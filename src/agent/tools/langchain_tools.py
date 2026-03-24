# LangChain Tools - 将现有工具转换为 LangChain StructuredTool
from typing import List, Optional
from pydantic import BaseModel, Field

from langchain_core.tools import StructuredTool

from agent.tools import (
    get_current_time,
    get_weather,
    add_todo,
    list_todos,
    complete_todo,
    get_clipboard,
    set_clipboard,
    get_system_info,
    open_application,
    edit_persona,
    play_motion,
    show_mood_emoji,
)
from agent.tools.mood_tool import get_all_available_types, MOOD_TYPES, CATEGORY_MOOD, CATEGORY_ACTION
from agent.tools.motion_tool import get_available_motions
from utils import get_logger

logger = get_logger()


# ============ 参数 Schema 定义 ============

class TimeToolArgs(BaseModel):
    """时间工具参数"""
    format: str = Field(
        default="%Y-%m-%d %H:%M:%S",
        description="时间格式，默认 %Y-%m-%d %H:%M:%S"
    )


class WeatherToolArgs(BaseModel):
    """天气工具参数"""
    city: str = Field(
        default="北京",
        description="城市名称"
    )


class AddTodoArgs(BaseModel):
    """添加待办参数"""
    content: str = Field(..., description="待办内容")
    due_date: Optional[str] = Field(None, description="截止日期，可选")


class ListTodosArgs(BaseModel):
    """列出待办参数"""
    only_pending: bool = Field(
        default=True,
        description="只显示未完成的"
    )


class CompleteTodoArgs(BaseModel):
    """完成待办参数"""
    item_id: str = Field(..., description="待办事项 ID")


class SetClipboardArgs(BaseModel):
    """设置剪贴板参数"""
    text: str = Field(..., description="要复制的文本")


class OpenAppArgs(BaseModel):
    """打开应用参数"""
    app_name: str = Field(..., description="应用名称或文件路径")


class EditPersonaArgs(BaseModel):
    """编辑角色设定参数"""
    action: str = Field(
        ...,
        description="操作类型: set_name, set_field, add_memory, add_fact, remove_memory, remove_fact"
    )
    field: Optional[str] = Field(
        None,
        description="字段名 (set_field 时使用): name, gender, age, personality, speech_style, first_person, second_person, user_nickname, relationship, background"
    )
    value: Optional[str] = Field(None, description="字段值")
    content: Optional[str] = Field(None, description="记忆内容 (add_memory 时使用)")
    key: Optional[str] = Field(None, description="事实键名 (add_fact/remove_fact 时使用)")
    confirm: bool = Field(default=False, description="是否已经过用户确认")


class PlayMotionArgs(BaseModel):
    """播放动作参数（动态 enum）"""
    motion_id: str = Field(
        ...,
        description="动作 ID，必须从可用动作列表中选择"
    )


class ShowMoodEmojiArgs(BaseModel):
    """显示心情/动作表情包参数（动态enum）"""
    mood: str = Field(
        ...,
        description="心情或动作类型"
    )
    
    @classmethod
    def get_available_types_desc(cls) -> str:
        """获取可用类型的描述"""
        types = get_all_available_types()
        if not types:
            return "心情或动作类型（暂无配置）"
        
        # 分类显示
        mood_types = []
        action_types = []
        for t in types:
            cn_name = MOOD_TYPES.get(t, t)
            if t in ["greeting", "cute", "attack", "hug", "kiss", "cry", "laugh", "doubt", "encourage", "celebrate"]:
                action_types.append(f"{t}({cn_name})")
            else:
                mood_types.append(f"{t}({cn_name})")
        
        desc_parts = []
        if mood_types:
            desc_parts.append(f"心情: {', '.join(mood_types)}")
        if action_types:
            desc_parts.append(f"动作: {', '.join(action_types)}")
        
        return " | ".join(desc_parts)


# ============ 创建 LangChain 工具 ============

def create_time_tool() -> StructuredTool:
    """创建时间工具"""
    return StructuredTool(
        name="get_current_time",
        description="获取当前时间、日期、星期几",
        args_schema=TimeToolArgs,
        coroutine=get_current_time,
    )


def create_weather_tool() -> StructuredTool:
    """创建天气工具"""
    return StructuredTool(
        name="get_weather",
        description="查询指定城市的天气情况",
        args_schema=WeatherToolArgs,
        coroutine=get_weather,
    )


def create_add_todo_tool() -> StructuredTool:
    """创建添加待办工具"""
    return StructuredTool(
        name="add_todo",
        description="添加待办事项",
        args_schema=AddTodoArgs,
        coroutine=add_todo,
    )


def create_list_todos_tool() -> StructuredTool:
    """创建列出待办工具"""
    return StructuredTool(
        name="list_todos",
        description="列出待办事项",
        args_schema=ListTodosArgs,
        coroutine=list_todos,
    )


def create_complete_todo_tool() -> StructuredTool:
    """创建完成待办工具"""
    return StructuredTool(
        name="complete_todo",
        description="标记待办事项为完成",
        args_schema=CompleteTodoArgs,
        coroutine=complete_todo,
    )


def create_get_clipboard_tool() -> StructuredTool:
    """创建获取剪贴板工具"""
    return StructuredTool(
        name="get_clipboard",
        description="获取当前剪贴板的内容",
        args_schema=BaseModel,
        coroutine=get_clipboard,
    )


def create_set_clipboard_tool() -> StructuredTool:
    """创建设置剪贴板工具"""
    return StructuredTool(
        name="set_clipboard",
        description="设置剪贴板内容",
        args_schema=SetClipboardArgs,
        coroutine=set_clipboard,
    )


def create_system_info_tool() -> StructuredTool:
    """创建系统信息工具"""
    return StructuredTool(
        name="get_system_info",
        description="获取 CPU、内存、磁盘使用情况",
        args_schema=BaseModel,
        coroutine=get_system_info,
    )


def create_launcher_tool() -> StructuredTool:
    """创建应用启动工具"""
    return StructuredTool(
        name="open_application",
        description="打开应用程序或文件",
        args_schema=OpenAppArgs,
        coroutine=open_application,
    )


def create_persona_tool() -> StructuredTool:
    """创建角色设定编辑工具"""
    return StructuredTool(
        name="edit_persona",
        description="修改角色设定、记忆、学到的信息。第一次启动时用于保存用户给的名字、关系等信息。重要修改前先询问用户确认。",
        args_schema=EditPersonaArgs,
        coroutine=edit_persona,
    )


def create_motion_tool() -> StructuredTool:
    """创建动作控制工具（动态生成 enum）"""
    # 动态获取可用动作（从模型配置文件读取）
    available_motions = get_available_motions()
    if not available_motions:
        available_motions = ["idle"]
        logger.warning("未找到可用动作，使用默认动作 [idle]")
    
    # 创建动态参数 Schema
    class DynamicPlayMotionArgs(BaseModel):
        """播放动作参数"""
        motion_id: str = Field(
            ...,
            description=f"动作 ID。可用: {', '.join(available_motions)}"
        )
    
    # 设置 enum
    DynamicPlayMotionArgs.model_fields['motion_id'].json_schema_extra = {"enum": available_motions}
    
    return StructuredTool(
        name="play_motion",
        description="播放 Live2D 模型动作。必须直接指定动作 ID，用于控制模型的肢体动作和表情动画。动作 ID 从模型的 .model3.json 文件动态读取。在回复文字前调用。",
        args_schema=DynamicPlayMotionArgs,
        coroutine=play_motion,
    )


def create_mood_emoji_tool() -> StructuredTool:
    """创建心情表情包工具（动态生成enum）"""
    # 动态获取可用类型
    available_types = get_all_available_types()
    if not available_types:
        available_types = ["happy"]
        logger.warning("未配置任何表情包，使用默认类型 [happy]")
    
    # 创建动态参数 Schema
    class DynamicShowMoodEmojiArgs(BaseModel):
        """显示心情/动作表情包参数"""
        mood: str = Field(
            ...,
            description=f"心情或动作类型。可用: {', '.join(available_types)}"
        )
    
    # 设置 enum
    DynamicShowMoodEmojiArgs.model_fields['mood'].json_schema_extra = {"enum": available_types}
    
    return StructuredTool(
        name="show_mood_emoji",
        description="显示心情或动作表情包气泡。在 Live2D 模型旁弹出表情包图片/GIF，用于更生动地表达情绪或执行动作。支持心情类型（开心、难过等）和动作类型（打招呼、撒娇等）。在回复文字前调用。",
        args_schema=DynamicShowMoodEmojiArgs,
        coroutine=show_mood_emoji,
    )


# ============ 工具工厂映射 ============

TOOL_FACTORIES = {
    "time": [create_time_tool],
    "weather": [create_weather_tool],
    "todo": [create_add_todo_tool, create_list_todos_tool, create_complete_todo_tool],
    "clipboard": [create_get_clipboard_tool, create_set_clipboard_tool],
    "system": [create_system_info_tool],
    "launcher": [create_launcher_tool],
    "persona_edit": [create_persona_tool],
    "motion_control": [create_motion_tool],
    "mood_emoji": [create_mood_emoji_tool],
}


def get_all_tools() -> List[StructuredTool]:
    """获取所有工具"""
    tools = []
    for factories in TOOL_FACTORIES.values():
        for factory in factories:
            tools.append(factory())
    return tools


def get_tools_by_ids(tool_ids: List[str]) -> List[StructuredTool]:
    """根据工具 ID 获取工具列表
    
    Args:
        tool_ids: 启用的工具 ID 列表
        
    Returns:
        StructuredTool 列表
    """
    tools = []
    for tool_id in tool_ids:
        if tool_id in TOOL_FACTORIES:
            for factory in TOOL_FACTORIES[tool_id]:
                tools.append(factory())
        else:
            logger.warning(f"未知工具 ID: {tool_id}")
    return tools
