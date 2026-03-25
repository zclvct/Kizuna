# Kizuna - 二次元桌面助手

<div align="center">

一个功能完整的 Live2D 二次元桌面助手，具备 AI 对话、角色设定、动态记忆、技能系统、心情驱动动作等功能。
使用claude code 与 codebuddy 开发

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Windows-lightgrey.svg)](https://github.com)

</div>

---

## ✨ 功能特性

### 🎭 Live2D 模型
- 支持 Live2D Cubism 3 模型
- 动态表情和动作播放
- 心情驱动的动画效果
- 可切换多个角色模型

### 🤖 AI 对话
- 支持多种 LLM 提供商（OpenAI、Ollama 等）
- 流式响应输出
- 上下文记忆管理
- 自定义角色设定

### 🧠 智能记忆
- 长期记忆存储
- 用户事实记录
- 语义搜索回忆
- 重要度评分系统

### 🔧 技能系统
- 内置工具：天气查询、待办事项、剪贴板、系统信息等
- MCP (Model Context Protocol) 扩展支持
- 可视化技能开关管理
- 定时任务调度

### 🎨 用户界面
- 现代化动漫风格 UI
- 系统托盘常驻
- 表情包气泡显示
- 多窗口设置面板

---

## 📦 安装

### 方式一：下载安装包（推荐）

从 [Releases](https://github.com/yourname/Kizuna/releases) 页面下载对应平台的安装包：

| 平台 | 文件 | 说明 |
|------|------|------|
| macOS | `Kizuna_macOS.dmg` | 双击安装 |
| Windows | `Kizuna_Windows.zip` | 解压运行 |

### 方式二：从源码运行

```bash
# 克隆仓库
git clone https://github.com/yourname/Kizuna.git
cd Kizuna

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt

# 运行
python run.py
```

---

## ⚙️ 配置

### LLM 配置

编辑 `data/config.json`：

```json
{
  "llm": {
    "default_provider": "openai",
    "providers": {
      "openai": {
        "api_key": "your-api-key",
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o-mini"
      },
      "ollama": {
        "base_url": "http://localhost:11434",
        "model": "llama3"
      }
    }
  }
}
```

### MCP 服务器配置

编辑 `data/mcp_servers.json`：

```json
{
  "servers": [
    {
      "id": "bing_search",
      "name": "Bing 搜索",
      "transport": "streamable_http",
      "url": "https://mcpmarket.cn/mcp/xxx",
      "enabled": true
    }
  ]
}
```

---

## 🎮 使用

### 基本操作

- **双击托盘图标**：显示/隐藏主窗口
- **右键托盘图标**：打开菜单
- **设置入口**：右键菜单 → 设置

### 角色设定

在设置页面可以自定义 AI 的：
- 名字、性别、年龄
- 性格特点、说话风格
- 自称、对用户的称呼
- 与用户的关系

### 技能管理

在设置页面可以：
- 开启/关闭内置技能
- 添加/编辑/删除 MCP 服务器
- 测试 MCP 工具

---

## 🏗️ 开发

### 项目结构

```
Kizuna/
├── assets/              # 资源文件
│   ├── images/          # 图片资源
│   └── live2d/          # Live2D 模型
├── data/                # 数据文件
│   ├── config.json      # 应用配置
│   ├── persona.json     # 角色设定
│   ├── mcp_servers.json # MCP 配置
│   └── memory.db        # 记忆数据库
├── src/                 # 源代码
│   ├── app/             # GUI 应用
│   ├── agent/           # AI Agent
│   │   ├── mcp/         # MCP 集成
│   │   ├── models/      # LLM 模型
│   │   ├── tools/       # 内置工具
│   │   └── memory/      # 记忆系统
│   └── live2d/          # Live2D 渲染
├── run.py               # 启动入口
├── requirements.txt     # Python 依赖
└── kizuna.spec          # PyInstaller 配置
```

### 本地打包

```bash
# macOS
./build_mac.sh

# Windows
build_win.bat

# 清理后重新打包
./build_mac.sh --clean
```

### 发布版本

```bash
# 创建 tag 触发 GitHub Actions 自动打包
./release.sh 1.0.0

# 或手动
git tag v1.0.0 && git push --tags
```

---

## 📋 系统要求

| 平台 | 最低版本 |
|------|----------|
| macOS | 10.13+ |
| Windows | 10+ |
| Python | 3.11+ |

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 🙏 致谢

- [Live2D](https://www.live2d.com/) - 虚拟角色技术
- [PySide6](https://doc.qt.io/qtforpython/) - GUI 框架
- [LangChain](https://www.langchain.com/) - LLM 框架
- [live2d-py](https://github.com/Arkueid/live2d-py) - Live2D Python 绑定

---

<div align="center">

**[⬆ 返回顶部](#kizuna---二次元桌面助手)**

</div>
