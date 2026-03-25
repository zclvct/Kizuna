# Scheduler Tool - 定时任务工具
import sys
from pathlib import Path
src_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_path))

from typing import Optional
from pydantic import BaseModel, Field

from utils import get_logger

logger = get_logger()


# ============ 参数 Schema ============

class CreateScheduledTaskArgs(BaseModel):
    """创建定时任务参数"""
    task_name: str = Field(
        ...,
        description="任务名称，简短描述，如 '每日新闻推送'"
    )
    cron_expression: str = Field(
        ...,
        description="Cron 表达式，格式：分 时 日 月 周。例如："
                    "'0 10 * * *' 表示每天10点，"
                    "'30 9 * * 1-5' 表示周一到周五9:30，"
                    "'0 */2 * * *' 表示每2小时"
    )
    action_prompt: str = Field(
        ...,
        description="任务执行时发送给 AI 的提示词，描述要执行的任务。"
                    "例如：'给用户推送今天的热点新闻'，'提醒用户开会'"
    )


# ============ 工具函数 ============

async def create_scheduled_task(
    task_name: str,
    cron_expression: str,
    action_prompt: str
) -> str:
    """创建定时任务，在指定时间自动执行。

    Args:
        task_name: 任务名称
        cron_expression: Cron 表达式
        action_prompt: 任务执行提示词

    Returns:
        创建结果消息
    """
    try:
        # 延迟导入，避免循环依赖
        from scheduler import get_task_manager

        # 验证 Cron 表达式格式
        parts = cron_expression.split()
        if len(parts) != 5:
            return f"❌ Cron 表达式格式错误！应为 5 个字段（分 时 日 月 周），实际 {len(parts)} 个字段"

        # 创建任务
        task_manager = get_task_manager()
        task = await task_manager.create_task(
            task_name=task_name,
            cron=cron_expression,
            action_prompt=action_prompt
        )

        # 格式化 Cron 为易读文本
        cron_text = _format_cron_human(cron_expression)

        logger.info(f"成功创建定时任务: {task_name} ({cron_expression})")

        return (
            f"✅ 定时任务创建成功！\n\n"
            f"📋 任务名称：{task_name}\n"
            f"⏰ 执行时间：{cron_text}\n"
            f"📝 任务内容：{action_prompt}\n\n"
            f"任务将在设定时间自动执行。你可以随时在设置 → 任务页面中查看和管理任务。"
        )

    except Exception as e:
        logger.error(f"创建定时任务失败: {e}")
        return f"❌ 创建失败：{str(e)}"


def _format_cron_human(cron: str) -> str:
    """将 Cron 表达式格式化为易读文本"""
    try:
        parts = cron.split()
        if len(parts) != 5:
            return cron
        
        minute, hour, day, month, weekday = parts
        
        # 常见模式识别
        if minute == "0" and hour != "*" and day == "*" and month == "*" and weekday == "*":
            return f"每天 {hour}:00"
        
        elif minute != "0" and hour != "*" and day == "*" and month == "*" and weekday == "*":
            return f"每天 {hour}:{minute.zfill(2)}"
        
        elif minute == "0" and hour != "*" and day == "*" and month == "*" and weekday != "*":
            weekdays = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"]
            if "," in weekday:
                # 处理多个工作日
                days = [weekdays[int(d)] for d in weekday.split(",")]
                return f"每{', '.join(days)} {hour}:00"
            elif "-" in weekday:
                # 处理工作日范围
                start, end = weekday.split("-")
                return f"每{weekdays[int(start)]}到{weekdays[int(end)]} {hour}:00"
            else:
                return f"每{weekdays[int(weekday)]} {hour}:00"
        
        elif minute == "0" and hour == "*" and day == "*" and month == "*" and weekday == "*":
            return "每小时整点"
        
        elif minute.startswith("*/") and hour != "*" and day == "*" and month == "*" and weekday == "*":
            interval = minute.split("*/")[1]
            return f"每 {hour} 点开始每隔 {interval} 分钟"
        
        elif minute == "0" and hour.startswith("*/") and day == "*" and month == "*" and weekday == "*":
            interval = hour.split("*/")[1]
            return f"每隔 {interval} 小时整点"
        
        else:
            return f"Cron: {cron}"
            
    except Exception:
        return cron


# ============ 工具定义（用于 LangChain）============

SCHEDULER_TOOL = {
    "type": "function",
    "function": {
        "name": "create_scheduled_task",
        "description": "创建定时任务，在指定时间自动执行。用户可以说 '每天10点提醒我开会' 来创建任务。",
        "parameters": {
            "type": "object",
            "properties": {
                "task_name": {
                    "type": "string",
                    "description": "任务名称，简短描述"
                },
                "cron_expression": {
                    "type": "string",
                    "description": "Cron 表达式，格式：分 时 日 月 周。例如 '0 10 * * *' 表示每天10点"
                },
                "action_prompt": {
                    "type": "string",
                    "description": "任务执行时发送给 AI 的提示词，描述要执行的任务"
                }
            },
            "required": ["task_name", "cron_expression", "action_prompt"]
        }
    }
}
