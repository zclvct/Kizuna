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
from agent.tools.memory_tool import (
    save_memory,
    save_fact,
    search_memory,
    get_user_facts,
    get_memory_stats,
)
from agent.tools.scheduler_tool import (
    create_scheduled_task,
    CreateScheduledTaskArgs,
)
from agent.tools.base import BaseToolArgs
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
        description="操作类型: set_name(设置名字), set_field(设置字段)"
    )
    field: Optional[str] = Field(
        None,
        description="字段名 (set_field 时必填): name(AI名字), gender(AI性别), age(AI年龄), personality(AI性格特点), "
                    "speech_style(AI说话风格), first_person(AI自称), second_person(AI对用户称呼), "
                    "user_nickname(用户昵称), relationship(与用户关系)"
    )
    value: str = Field(..., description="要设置的值")
    confirm: bool = Field(
        default=False,
        description="是否已经过用户确认（重要字段修改时需要）"
    )


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
        description="""【AI角色设定】设置 AI 自己的角色属性。仅用于设置 AI 本身的设定，不存储用户信息！

可用操作：
- set_name: 设置 AI 的名字
- set_field: 设置 AI 的属性字段

可设置的字段（都是AI自己的属性）：
- name: AI的名字
- gender: AI的性别  
- age: AI的年龄
- personality: AI的性格特点
- speech_style: AI的说话风格
- first_person: AI的自称（如"我"、"本喵"）
- second_person: AI对用户的称呼（如"主人"、"你"）
- user_nickname: 用户在AI心中的昵称
- relationship: AI与用户的关系

【重要】用户的信息（姓名、爱好、喜欢吃什么等）请使用 save_fact 工具！""",
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


# ============ 记忆工具参数 Schema ============

class SaveMemoryArgs(BaseModel):
    """保存记忆参数"""
    content: str = Field(description="记忆内容")
    importance: int = Field(default=3, ge=1, le=5, description="重要性 (1-5)")


class SaveFactArgs(BaseModel):
    """保存事实参数"""
    key: str = Field(description='事实键名（如"姓名"、"职业"、"爱好"）')
    value: str = Field(description="事实值")


class SearchMemoryArgs(BaseModel):
    """搜索记忆参数"""
    query: str = Field(description="搜索关键词")
    limit: int = Field(default=5, ge=1, le=20, description="返回结果数量")


# ============ 记忆工具工厂 ============

def create_save_memory_tool() -> StructuredTool:
    """创建保存记忆工具"""
    return StructuredTool(
        name="save_memory",
        description="""保存重要记忆到长期记忆库。

使用场景：
- 用户提到重要事件、纪念日、里程碑
- 用户表达重要偏好或习惯
- 用户分享重要的个人信息
- 有情感价值的重要对话

重要性评分：
- 5分：极其重要，必须记住
- 4分：很重要，会影响未来互动
- 3分：有价值，值得记住（默认）""",
        args_schema=SaveMemoryArgs,
        coroutine=save_memory,
    )


def create_save_fact_tool() -> StructuredTool:
    """创建保存事实工具"""
    return StructuredTool(
        name="save_fact",
        description="""【用户信息】保存关于用户的事实信息。用于记录用户的信息和偏好！

使用场景：
- 用户分享姓名、年龄、职业等基本信息
- 用户提到兴趣爱好、喜欢吃什么、讨厌什么
- 用户透露住址、联系方式
- 用户提到家庭成员、朋友

key 必须使用中文：
- key="喜欢的食物" value="鸡腿"
- key="姓名" value="张三"
- key="职业" value="程序员"

事实应该简洁明了、准确无误、长期有效。""",
        args_schema=SaveFactArgs,
        coroutine=save_fact,
    )


def create_search_memory_tool() -> StructuredTool:
    """创建搜索记忆工具"""
    return StructuredTool(
        name="search_memory",
        description="""从长期记忆库中搜索相关记忆和用户事实。

使用场景：
- 用户询问"我喜欢吃什么"、"我叫什么"等
- 需要回忆用户之前提到的信息
- 查找相关的历史记忆

支持中文关键词搜索，如"喜欢吃什么"、"名字"、"职业"等。""",
        args_schema=SearchMemoryArgs,
        coroutine=search_memory,
    )


def create_get_facts_tool() -> StructuredTool:
    """创建获取事实工具"""
    return StructuredTool(
        name="get_user_facts",
        description="获取已记录的用户事实信息。用于了解用户的基本信息和偏好。",
        args_schema=BaseToolArgs,
        coroutine=get_user_facts,
    )


def create_get_memory_stats_tool() -> StructuredTool:
    """创建获取记忆统计工具"""
    return StructuredTool(
        name="get_memory_stats",
        description="获取记忆系统的统计信息，包括总记忆数、总事实数等。",
        args_schema=BaseToolArgs,
        coroutine=get_memory_stats,
    )


def create_scheduled_task_tool() -> StructuredTool:
    """创建定时任务工具"""
    return StructuredTool(
        name="create_scheduled_task",
        description="创建定时任务，在指定时间自动执行。用户可以说 '每天10点提醒我开会' 来创建任务。",
        args_schema=CreateScheduledTaskArgs,
        coroutine=create_scheduled_task,
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
    "scheduler": [create_scheduled_task_tool],
    "memory": [
        create_save_memory_tool,
        create_save_fact_tool,
        create_search_memory_tool,
        create_get_facts_tool,
        create_get_memory_stats_tool,
    ],
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
