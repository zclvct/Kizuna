# Pure Tools - StructuredTool ↔ litellm/OpenAI function calling 格式转换
import json
from typing import List, Dict

from langchain_core.tools import StructuredTool

from utils import get_logger

logger = get_logger()


def structured_tools_to_litellm(tools: List[StructuredTool]) -> List[dict]:
    """将 LangChain StructuredTool 列表转换为 litellm tools 格式

    litellm 使用 OpenAI function calling 格式：
    {
        "type": "function",
        "function": {
            "name": "...",
            "description": "...",
            "parameters": {
                "type": "object",
                "properties": {...},
                "required": [...]
            }
        }
    }

    Args:
        tools: LangChain StructuredTool 列表

    Returns:
        litellm tools 格式列表
    """
    result = []
    for tool in tools:
        schema = {"type": "object", "properties": {}, "required": []}
        if tool.args_schema:
            try:
                raw_schema = tool.args_schema.schema()
                properties = raw_schema.get("properties", {})
                # 移除 Pydantic 内部字段
                properties = {
                    k: v for k, v in properties.items()
                    if k not in ("title",)
                }
                # 清理每个属性中的 title（冗余信息）
                cleaned_props = {}
                for prop_name, prop_val in properties.items():
                    cleaned_val = {k: v for k, v in prop_val.items() if k != "title"}
                    cleaned_props[prop_name] = cleaned_val

                required = raw_schema.get("required", [])
                schema = {
                    "type": "object",
                    "properties": cleaned_props,
                    "required": required,
                }
            except (AttributeError, TypeError):
                # args_schema 是 BaseModel 本身而非子类，无参数
                pass

        result.append({
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description or "",
                "parameters": schema,
            }
        })

    return result


async def execute_tool_call(
    tool_call: dict,
    tool_map: Dict[str, StructuredTool]
) -> str:
    """执行 litellm 返回的 tool_call

    Args:
        tool_call: litellm 格式的 tool_call
            {
                "id": "call_xxx",
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "arguments": '{"city": "北京"}'
                }
            }
        tool_map: 工具名 → StructuredTool 映射

    Returns:
        工具执行结果字符串
    """
    function_name = tool_call["function"]["name"]
    arguments_str = tool_call["function"]["arguments"]

    try:
        arguments = json.loads(arguments_str) if arguments_str else {}
    except json.JSONDecodeError:
        logger.error(f"工具参数 JSON 解析失败: {arguments_str}")
        return "Error: 无法解析工具参数"

    tool = tool_map.get(function_name)
    if not tool:
        logger.error(f"未知工具: {function_name}")
        return f"Error: 未知工具 '{function_name}'"

    try:
        # 优先使用 coroutine（异步方法）
        if tool.coroutine:
            result = await tool.coroutine(**arguments)
        elif tool.func:
            result = tool.func(**arguments)
        else:
            result = "Error: 工具无可用执行函数"

        return str(result)

    except Exception as e:
        logger.error(f"工具执行错误 {function_name}: {e}", exc_info=True)
        return f"Error: {str(e)}"
