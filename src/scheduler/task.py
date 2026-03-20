# Scheduled Task Model
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import uuid4


class ScheduledTask(BaseModel):
    """定时任务模型"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    task_name: str = ""
    cron: str = ""
    action_prompt: str = ""
    motion_id: Optional[str] = None
    enabled: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Function Calling 工具定义
CREATE_SCHEDULED_TASK_TOOL = {
    "type": "function",
    "function": {
        "name": "create_scheduled_task",
        "description": "创建定时任务。Cron 表达式格式：分 时 日 月 周",
        "parameters": {
            "type": "object",
            "properties": {
                "cron": {
                    "type": "string",
                    "description": "Cron 表达式，格式：分 时 日 月 周，例如 0 10 * * * 表示每天10点"
                },
                "task_name": {
                    "type": "string",
                    "description": "任务名称，简短描述"
                },
                "action_prompt": {
                    "type": "string",
                    "description": "任务执行时发送给 LLM 的 Prompt"
                },
                "motion_id": {
                    "type": "string",
                    "description": "可选，任务执行时 Live2D 的动作 ID"
                }
            },
            "required": ["cron", "task_name", "action_prompt"]
        }
    }
}
