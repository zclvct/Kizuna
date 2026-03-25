# Tool Registry - LangChain 工具注册器
from typing import Dict, List, Optional
import asyncio

from langchain_core.tools import StructuredTool

from agent.tools.langchain_tools import TOOL_FACTORIES, get_tools_by_ids
from agent.config import get_app_config
from utils import get_logger

logger = get_logger()


class ToolRegistry:
    """LangChain 工具注册器
    
    管理工具的注册、启用/禁用、获取等操作
    支持内置工具和 MCP 工具
    """
    
    _instance: Optional["ToolRegistry"] = None
    
    def __init__(self):
        self._tools: Dict[str, StructuredTool] = {}
        self._tool_to_group: Dict[str, str] = {}  # tool_name -> group_id
        self._mcp_tools: List[StructuredTool] = []  # MCP 工具缓存
        self._register_all()
    
    @classmethod
    def get_instance(cls) -> "ToolRegistry":
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def _register_all(self):
        """注册所有内置工具"""
        for group_id, factories in TOOL_FACTORIES.items():
            for factory in factories:
                tool = factory()
                self._tools[tool.name] = tool
                self._tool_to_group[tool.name] = group_id
        logger.info(f"已注册 {len(self._tools)} 个内置工具")
    
    def get_tool(self, name: str) -> Optional[StructuredTool]:
        """获取单个工具"""
        return self._tools.get(name)
    
    def get_all_tools(self) -> List[StructuredTool]:
        """获取所有内置工具"""
        return list(self._tools.values())
    
    def get_enabled_tools(self) -> List[StructuredTool]:
        """获取启用的内置工具列表
        
        根据应用配置中的工具启用状态过滤
        """
        config = get_app_config()
        enabled_group_ids = set(config.get_enabled_tool_ids())
        
        enabled_tools = []
        for tool_name, tool in self._tools.items():
            group_id = self._tool_to_group.get(tool_name)
            if group_id in enabled_group_ids:
                enabled_tools.append(tool)
        
        logger.info(f"启用的内置工具: {len(enabled_tools)}/{len(self._tools)}")
        return enabled_tools
    
    async def get_mcp_tools(self, force_reload: bool = False) -> List[StructuredTool]:
        """获取 MCP 工具列表
        
        Args:
            force_reload: 是否强制重新加载
            
        Returns:
            MCP 工具列表
        """
        try:
            from agent.mcp import get_mcp_manager
            manager = get_mcp_manager()
            self._mcp_tools = await manager.load_tools(force_reload=force_reload)
            return self._mcp_tools
        except ImportError:
            logger.warning("MCP 模块未安装，跳过 MCP 工具加载")
            return []
        except Exception as e:
            logger.error(f"加载 MCP 工具失败: {e}")
            return []
    
    def get_mcp_tools_sync(self) -> List[StructuredTool]:
        """同步获取已缓存的 MCP 工具"""
        return self._mcp_tools
    
    async def get_all_enabled_tools(self) -> List[StructuredTool]:
        """获取所有启用的工具（内置 + MCP）
        
        这是异步版本，会加载 MCP 工具
        """
        builtin_tools = self.get_enabled_tools()
        mcp_tools = await self.get_mcp_tools()
        
        all_tools = builtin_tools + mcp_tools
        logger.info(f"总工具数: {len(all_tools)} (内置: {len(builtin_tools)}, MCP: {len(mcp_tools)})")
        return all_tools
    
    def get_tools_for_agent(self) -> List[StructuredTool]:
        """获取供 Agent 使用的工具列表（同步版本）
        
        注意：此方法只返回内置工具，MCP 工具需要通过异步方法获取
        """
        return self.get_enabled_tools()
    
    async def get_tools_for_agent_async(self) -> List[StructuredTool]:
        """获取供 Agent 使用的工具列表（异步版本）
        
        包含内置工具和 MCP 工具
        """
        return await self.get_all_enabled_tools()
    
    def is_tool_enabled(self, tool_name: str) -> bool:
        """检查工具是否启用"""
        group_id = self._tool_to_group.get(tool_name)
        if not group_id:
            return False
        
        config = get_app_config()
        return config.is_tool_enabled(group_id)
    
    def get_tool_names(self) -> List[str]:
        """获取所有内置工具名称"""
        return list(self._tools.keys())
    
    def get_mcp_tool_names(self) -> List[str]:
        """获取 MCP 工具名称"""
        return [tool.name for tool in self._mcp_tools]
    
    def reload_mcp_tools(self):
        """重新加载 MCP 工具（异步包装）"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self.get_mcp_tools(force_reload=True))
            else:
                loop.run_until_complete(self.get_mcp_tools(force_reload=True))
        except RuntimeError:
            asyncio.run(self.get_mcp_tools(force_reload=True))


# 全局注册器实例
_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """获取全局工具注册器"""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry
