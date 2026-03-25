# MCP 集成执行计划（基于 langchain-mcp-adapters）

## 一、整体架构

```
┌─────────────────────────────────────────────────────────┐
│                     设置窗口                              │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐                    │
│  │ LLM 设置│ │工具设置 │ │ MCP 设置│                    │
│  └─────────┘ └─────────┘ └─────────┘                    │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                   工具注册中心                            │
│  ┌─────────────┐  ┌─────────────────────────┐          │
│  │ 内置工具    │  │ MCP → LangChain 适配器  │          │
│  │ (registry)  │  │ (langchain-mcp-adapters)│          │
│  └─────────────┘  └─────────────────────────┘          │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                    MCP Servers                           │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐             │
│  │ filesystem│ │ websearch │ │ brave-search│ ...        │
│  └───────────┘ └───────────┘ └───────────┘             │
└─────────────────────────────────────────────────────────┘
```

## 二、依赖项

```txt
langchain-mcp-adapters>=0.1.0  # MCP → LangChain 适配器
mcp>=0.9.0                    # MCP Python SDK（可选，适配器已包含）
```

## 三、模块设计

### 1. 数据层

| 文件 | 说明 |
|------|------|
| `data/mcp_servers.json` | MCP 服务器配置 |

**配置结构：**
```json
{
  "servers": [
    {
      "id": "filesystem",
      "name": "文件系统",
      "transport": "stdio",
      "command": "mcp-server-filesystem",
      "args": ["/Users/xxx/workspace"],
      "env": {},
      "enabled": true
    },
    {
      "id": "brave-search",
      "name": "Brave搜索",
      "transport": "stdio", 
      "command": "mcp-server-brave-search",
      "args": [],
      "env": {"BRAVE_API_KEY": "xxx"},
      "enabled": true
    },
    {
      "id": "remote-server",
      "name": "远程服务",
      "transport": "sse",
      "url": "http://localhost:8080/sse",
      "enabled": true
    }
  ]
}
```

### 2. MCP 模块 (`src/agent/mcp/`)

| 文件 | 说明 |
|------|------|
| `__init__.py` | 模块入口，导出核心类 |
| `config.py` | `MCPServerConfig` 配置管理类 |
| `manager.py` | MCP 连接管理器（使用 langchain-mcp-adapters） |

**核心逻辑（简化）：**
```python
# manager.py - 伪代码示意
from langchain_mcp_adapters import load_mcp_tools

async def get_mcp_tools(servers_config):
    """获取所有 MCP 工具"""
    tools = []
    for server in servers_config:
        if server.enabled:
            server_tools = await load_mcp_tools(
                command=server.command,
                args=server.args,
                env=server.env
            )
            tools.extend(server_tools)
    return tools
```

### 3. UI 层

| 文件 | 说明 |
|------|------|
| `mcp_page.py` | MCP 设置页面（添加/编辑/删除服务器配置） |

### 4. 工具注册增强

| 修改文件 | 说明 |
|----------|------|
| `src/agent/tools/registry.py` | 增加 MCP 工具获取方法 |
| `src/agent/core.py` | 初始化时加载 MCP 工具 |

## 四、执行步骤

### 阶段一：基础配置

| 步骤 | 任务 | 产出 |
|------|------|------|
| 1.1 | 创建 `data/mcp_servers.json` | 空配置文件 |
| 1.2 | 创建 `src/agent/mcp/__init__.py` | 模块入口 |
| 1.3 | 创建 `src/agent/mcp/config.py` | 配置读写类 |
| 1.4 | 更新 `requirements.txt` | 添加依赖 |

### 阶段二：MCP 管理器

| 步骤 | 任务 | 产出 |
|------|------|------|
| 2.1 | 创建 `src/agent/mcp/manager.py` | MCP 工具加载器（基于适配器） |
| 2.2 | 修改 `src/agent/tools/registry.py` | 增加 `get_mcp_tools()` 方法 |

### 阶段三：设置页面

| 步骤 | 任务 | 产出 |
|------|------|------|
| 3.1 | 创建 `src/app/settings/mcp_page.py` | MCP 设置页面 UI |
| 3.2 | 修改 `settings_window.py` | 添加 MCP 标签页 |

### 阶段四：核心集成

| 步骤 | 任务 | 产出 |
|------|------|------|
| 4.1 | 修改 `src/agent/core.py` | 初始化时加载 MCP 工具 |
| 4.2 | 修改 `src/agent/agent.py` | 支持动态工具更新 |

### 阶段五：LLM 页面增强（可选）

| 步骤 | 任务 | 产出 |
|------|------|------|
| 5.1 | 修改 `llm_page.py` | 显示当前启用的 MCP 工具数量/列表 |

## 五、关键代码示意

```python
# src/agent/mcp/manager.py
from langchain_mcp_adapters import load_mcp_tools
from langchain_core.tools import StructuredTool

class MCPToolManager:
    """MCP 工具管理器"""
    
    def __init__(self, config: MCPServerConfig):
        self.config = config
    
    async def load_tools(self) -> list[StructuredTool]:
        """加载所有启用的 MCP 工具"""
        all_tools = []
        for server in self.config.get_enabled_servers():
            tools = await load_mcp_tools(
                command=server.command,
                args=server.args,
                env=server.env
            )
            all_tools.extend(tools)
        return all_tools
```

## 六、对比原方案优势

| 项目 | 原方案（手写桥接） | 新方案（langchain-mcp-adapters） |
|------|-------------------|----------------------------------|
| 代码量 | ~200 行桥接代码 | ~50 行调用代码 |
| 维护成本 | 需跟随 MCP 协议更新 | 由适配器库维护 |
| 稳定性 | 需自行测试 | 社区验证 |
| 协议支持 | 需手动实现 stdio/sse | 开箱即用 |
