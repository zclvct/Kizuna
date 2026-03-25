# MCP Config - MCP 服务器配置管理
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field, asdict
from pathlib import Path
import json

from utils import get_logger

logger = get_logger()


@dataclass
class MCPServer:
    """MCP 服务器配置"""
    id: str
    name: str
    transport: str = "stdio"  # stdio | sse | streamable_http
    command: str = ""
    args: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)
    url: str = ""  # SSE/streamable_http 传输时使用
    enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MCPServer":
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            transport=data.get("transport", "stdio"),
            command=data.get("command", ""),
            args=data.get("args", []),
            env=data.get("env", {}),
            url=data.get("url", ""),
            enabled=data.get("enabled", True),
        )


class MCPServerConfig:
    """MCP 服务器配置管理"""
    
    _instance: Optional["MCPServerConfig"] = None
    
    def __init__(self):
        self._config_path = Path(__file__).parent.parent.parent.parent / "data" / "mcp_servers.json"
        self.servers: List[MCPServer] = []
        self._load()
    
    @classmethod
    def get_instance(cls) -> "MCPServerConfig":
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def _load(self):
        """加载配置"""
        if not self._config_path.exists():
            self.servers = []
            self.save()
            return
        
        try:
            with open(self._config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            self.servers = [
                MCPServer.from_dict(s) for s in data.get("servers", [])
            ]
            logger.info(f"已加载 {len(self.servers)} 个 MCP 服务器配置")
        except Exception as e:
            logger.error(f"加载 MCP 配置失败: {e}")
            self.servers = []
    
    def save(self):
        """保存配置"""
        try:
            data = {
                "servers": [s.to_dict() for s in self.servers]
            }
            
            self._config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self._config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info("MCP 配置已保存")
        except Exception as e:
            logger.error(f"保存 MCP 配置失败: {e}")
            raise
    
    def get_server(self, server_id: str) -> Optional[MCPServer]:
        """获取服务器配置"""
        for server in self.servers:
            if server.id == server_id:
                return server
        return None
    
    def get_enabled_servers(self) -> List[MCPServer]:
        """获取所有启用的服务器"""
        return [s for s in self.servers if s.enabled]
    
    def add_server(self, server: MCPServer):
        """添加服务器"""
        # 检查 ID 是否重复
        if self.get_server(server.id):
            raise ValueError(f"服务器 ID '{server.id}' 已存在")
        
        self.servers.append(server)
        self.save()
        logger.info(f"已添加 MCP 服务器: {server.name}")
    
    def update_server(self, server_id: str, server: MCPServer):
        """更新服务器配置"""
        for i, s in enumerate(self.servers):
            if s.id == server_id:
                self.servers[i] = server
                self.save()
                logger.info(f"已更新 MCP 服务器: {server.name}")
                return
        raise ValueError(f"服务器 '{server_id}' 不存在")
    
    def remove_server(self, server_id: str):
        """删除服务器"""
        for i, s in enumerate(self.servers):
            if s.id == server_id:
                removed = self.servers.pop(i)
                self.save()
                logger.info(f"已删除 MCP 服务器: {removed.name}")
                return
        raise ValueError(f"服务器 '{server_id}' 不存在")
    
    def toggle_server(self, server_id: str, enabled: bool):
        """启用/禁用服务器"""
        server = self.get_server(server_id)
        if server:
            server.enabled = enabled
            self.save()
            status = "启用" if enabled else "禁用"
            logger.info(f"已{status} MCP 服务器: {server.name}")


def get_mcp_config() -> MCPServerConfig:
    """获取 MCP 配置实例"""
    return MCPServerConfig.get_instance()
