# Function Calling Handler
import sys
from pathlib import Path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from typing import Dict, Any, List, Optional, Tuple
import json

from assistant.tool_registry import get_tool_registry
from utils import get_logger

logger = get_logger()


class FunctionCallingHandler:
    """Function Calling 处理器"""

    def __init__(self):
        self.registry = get_tool_registry()
        self.tool_results = []  # 存储工具结果

    async def process_tool_calls(self, message) -> Tuple[Optional[str], List[Dict]]:
        """
        处理 tool calls

        返回: (需要确认的消息, 工具结果列表)
        """
        self.tool_results = []  # 清空之前的结果

        if not hasattr(message, 'tool_calls') or not message.tool_calls:
            return None, []

        needs_confirm = None

        for tool_call in message.tool_calls:
            name = tool_call.function.name
            try:
                arguments = json.loads(tool_call.function.arguments)
            except Exception as e:
                logger.error(f"Failed to parse tool arguments: {e}")
                continue

            try:
                result = await self.registry.execute(name, arguments)

                # 检查是否需要确认
                if result.get("status") == "needs_confirm":
                    needs_confirm = result.get("message")
                else:
                    self.tool_results.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": name,
                        "content": json.dumps(result, ensure_ascii=False)
                    })

            except Exception as e:
                logger.error(f"Tool execution failed: {name}, error: {e}")
                self.tool_results.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": name,
                    "content": json.dumps({"error": str(e), "success": False})
                })

        return needs_confirm, self.tool_results

    def get_tools(self) -> List[Dict]:
        """获取所有工具定义"""
        return self.registry.to_openai_tools()


# 全局处理器
_function_handler: Optional[FunctionCallingHandler] = None


def get_function_handler() -> FunctionCallingHandler:
    """获取 Function Calling 处理器"""
    global _function_handler
    if _function_handler is None:
        _function_handler = FunctionCallingHandler()
    return _function_handler
