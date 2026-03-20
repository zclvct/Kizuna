# Task Parser (LLM-driven)
import sys
from pathlib import Path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from typing import Optional, Dict, Any
import json

from scheduler.task import CREATE_SCHEDULED_TASK_TOOL
from utils import get_logger

logger = get_logger()


class TaskParser:
    """LLM 驱动的任务解析器"""

    SYSTEM_PROMPT = """你是一个定时任务解析器。将用户的自然语言描述转换为定时任务配置。

Cron 表达式格式：分 时 日 月 周
- * 表示任意值
- , 分隔多个值
- - 表示范围
- / 表示间隔

示例：
- "每天早上8点" → "0 8 * * *"
- "每周一早上9点" → "0 9 * * 1"
- "每2小时" → "0 */2 * * *"
- "每月1号10点" → "0 10 1 * *"

只返回 JSON，不要其他文字。"""

    def __init__(self, llm_client):
        self.llm_client = llm_client

    async def parse(self, user_input: str) -> Optional[Dict[str, Any]]:
        """解析用户输入为任务配置"""
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": user_input}
        ]

        try:
            response = await self.llm_client.chat(
                messages,
                tools=[CREATE_SCHEDULED_TASK_TOOL]
            )

            if hasattr(response, 'choices') and response.choices[0].message.tool_calls:
                tool_call = response.choices[0].message.tool_calls[0]
                return json.loads(tool_call.function.arguments)

            return None
        except Exception as e:
            logger.error(f"解析定时任务失败: {e}")
            return None
