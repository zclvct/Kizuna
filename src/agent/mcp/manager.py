# MCP Manager - MCP 工具管理器
from typing import List, Optional, Dict, Any
import asyncio

from langchain_core.tools import StructuredTool

from .config import MCPServer, get_mcp_config
from utils import get_logger

logger = get_logger()

# 延迟导入，避免未安装时报错
_mcp_adapters = None


def _get_mcp_adapters():
    """延迟导入 langchain-mcp-adapters"""
    global _mcp_adapters
    if _mcp_adapters is None:
        try:
            from langchain_mcp_adapters.tools import load_mcp_tools
            _mcp_adapters = load_mcp_tools
        except ImportError:
            logger.warning("langchain-mcp-adapters 未安装，MCP 功能不可用")
            _mcp_adapters = False
    return _mcp_adapters if _mcp_adapters else None


class MCPToolManager:
    """MCP 工具管理器
    
    负责加载和管理来自 MCP 服务器的工具
    """
    
    _instance: Optional["MCPToolManager"] = None
    
    def __init__(self):
        self.config = get_mcp_config()
        self._tools: List[StructuredTool] = []
        self._loaded = False
    
    @classmethod
    def get_instance(cls) -> "MCPToolManager":
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    async def load_tools(self, force_reload: bool = False) -> List[StructuredTool]:
        """加载所有启用的 MCP 工具
        
        Args:
            force_reload: 是否强制重新加载
            
        Returns:
            工具列表
        """
        if self._loaded and not force_reload:
            return self._tools
        
        load_mcp_tools = _get_mcp_adapters()
        if not load_mcp_tools:
            logger.warning("MCP 适配器不可用，跳过加载")
            return []
        
        self._tools = []
        enabled_servers = self.config.get_enabled_servers()
        
        if not enabled_servers:
            logger.info("没有启用的 MCP 服务器")
            return []
        
        logger.info(f"开始加载 {len(enabled_servers)} 个 MCP 服务器的工具...")
        
        for server in enabled_servers:
            try:
                tools = await self._load_server_tools(server, load_mcp_tools)
                self._tools.extend(tools)
                logger.info(f"MCP 服务器 '{server.name}' 加载了 {len(tools)} 个工具")
            except* Exception as eg:
                # Python 3.11+ ExceptionGroup 处理（同时捕获普通异常和 ExceptionGroup）
                error_msgs = [str(exc) for exc in eg.exceptions]
                logger.error(f"加载 MCP 服务器 '{server.name}' 失败: {'; '.join(error_msgs)}")
        
        self._loaded = True
        logger.info(f"MCP 工具加载完成，共 {len(self._tools)} 个工具")
        return self._tools
    
    async def _load_server_tools(
        self, 
        server: MCPServer,
        load_func
    ) -> List[StructuredTool]:
        """加载单个服务器的工具
        
        Args:
            server: 服务器配置
            load_func: 加载函数 (langchain_mcp_adapters.tools.load_mcp_tools)
            
        Returns:
            工具列表
        """
        if server.transport == "stdio":
            # stdio 传输模式
            connection = {
                "transport": "stdio",
                "command": server.command,
                "args": server.args if server.args else []
            }
            if server.env:
                connection["env"] = server.env
            tools = await load_func(session=None, connection=connection)
        elif server.transport == "sse":
            # SSE 传输模式
            connection = {
                "transport": "sse",
                "url": server.url
            }
            tools = await load_func(session=None, connection=connection)
        elif server.transport == "streamable_http":
            # Streamable HTTP 传输模式
            connection = {
                "transport": "streamable_http",
                "url": server.url
            }
            tools = await load_func(session=None, connection=connection)
        else:
            logger.warning(f"未知的传输类型: {server.transport}")
            tools = []
        
        return tools
    
    def get_tools(self) -> List[StructuredTool]:
        """获取已加载的工具（同步方法）"""
        return self._tools
    
    def reload(self):
        """重新加载工具（异步包装）"""
        self._loaded = False
        # 在事件循环中执行
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果循环正在运行，创建任务
                asyncio.create_task(self.load_tools(force_reload=True))
            else:
                # 否则直接运行
                loop.run_until_complete(self.load_tools(force_reload=True))
        except RuntimeError:
            # 没有事件循环，创建新的
            asyncio.run(self.load_tools(force_reload=True))
    
    def get_tool_names(self) -> List[str]:
        """获取工具名称列表"""
        return [tool.name for tool in self._tools]
    
    def is_available(self) -> bool:
        """检查 MCP 功能是否可用"""
        return _get_mcp_adapters() is not None


def get_mcp_manager() -> MCPToolManager:
    """获取全局 MCP 管理器实例"""
    return MCPToolManager.get_instance()


async def get_mcp_tools() -> List[StructuredTool]:
    """便捷函数：获取 MCP 工具列表"""
    manager = get_mcp_manager()
    return await manager.load_tools()
