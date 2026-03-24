# LangChain Tool Base
from abc import ABC
from typing import Type, Optional, Callable, Awaitable, Any
from pydantic import BaseModel

from langchain_core.tools import StructuredTool

from utils import get_logger

logger = get_logger()


class BaseToolArgs(BaseModel):
    """工具参数基类"""
    pass


class LangChainTool(ABC):
    """LangChain 工具基类
    
    提供便捷的方法将自定义工具转换为 LangChain StructuredTool
    """
    
    name: str = ""
    description: str = ""
    args_schema: Type[BaseModel] = BaseToolArgs
    
    @classmethod
    def execute(cls, **kwargs) -> Any:
        """同步执行方法，子类应覆盖"""
        raise NotImplementedError
    
    @classmethod
    async def aexecute(cls, **kwargs) -> Any:
        """异步执行方法，子类应覆盖"""
        raise NotImplementedError
    
    @classmethod
    def to_structured_tool(cls) -> StructuredTool:
        """转换为 LangChain StructuredTool"""
        
        async def _acoroutine(**kwargs):
            return await cls.aexecute(**kwargs)
        
        return StructuredTool(
            name=cls.name,
            description=cls.description,
            args_schema=cls.args_schema,
            coroutine=_acoroutine,
        )


def create_tool_from_function(
    name: str,
    description: str,
    func: Callable[..., Awaitable[Any]],
    args_schema: Type[BaseModel],
) -> StructuredTool:
    """从函数创建 LangChain 工具
    
    Args:
        name: 工具名称
        description: 工具描述
        func: 异步函数
        args_schema: 参数 Schema
        
    Returns:
        StructuredTool 实例
    """
    return StructuredTool(
        name=name,
        description=description,
        args_schema=args_schema,
        coroutine=func,
    )
