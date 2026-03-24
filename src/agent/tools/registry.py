# Tool Registry - LangChain 工具注册器
from typing import Dict, List, Optional
from pathlib import Path

from langchain_core.tools import StructuredTool

from agent.tools.langchain_tools import TOOL_FACTORIES, get_tools_by_ids
from agent.config import get_app_config
from utils import get_logger

logger = get_logger()


class ToolRegistry:
    """LangChain 工具注册器
    
    管理工具的注册、启用/禁用、获取等操作
    """
    
    _instance: Optional["ToolRegistry"] = None
    
    def __init__(self):
        self._tools: Dict[str, StructuredTool] = {}
        self._tool_to_group: Dict[str, str] = {}  # tool_name -> group_id
        self._register_all()
    
    @classmethod
    def get_instance(cls) -> "ToolRegistry":
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def _register_all(self):
        """注册所有工具"""
        for group_id, factories in TOOL_FACTORIES.items():
            for factory in factories:
                tool = factory()
                self._tools[tool.name] = tool
                self._tool_to_group[tool.name] = group_id
        logger.info(f"已注册 {len(self._tools)} 个工具")
    
    def get_tool(self, name: str) -> Optional[StructuredTool]:
        """获取单个工具"""
        return self._tools.get(name)
    
    def get_all_tools(self) -> List[StructuredTool]:
        """获取所有工具"""
        return list(self._tools.values())
    
    def get_enabled_tools(self) -> List[StructuredTool]:
        """获取启用的工具列表
        
        根据应用配置中的工具启用状态过滤
        """
        config = get_app_config()
        enabled_group_ids = set(config.get_enabled_tool_ids())
        
        enabled_tools = []
        for tool_name, tool in self._tools.items():
            group_id = self._tool_to_group.get(tool_name)
            if group_id in enabled_group_ids:
                enabled_tools.append(tool)
        
        logger.info(f"启用的工具: {len(enabled_tools)}/{len(self._tools)}")
        return enabled_tools
    
    def get_tools_for_agent(self) -> List[StructuredTool]:
        """获取供 Agent 使用的工具列表
        
        这是主要入口，返回所有启用的工具
        """
        return self.get_enabled_tools()
    
    def is_tool_enabled(self, tool_name: str) -> bool:
        """检查工具是否启用"""
        group_id = self._tool_to_group.get(tool_name)
        if not group_id:
            return False
        
        config = get_app_config()
        return config.is_tool_enabled(group_id)
    
    def get_tool_names(self) -> List[str]:
        """获取所有工具名称"""
        return list(self._tools.keys())


# 全局注册器实例
_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """获取全局工具注册器"""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry
