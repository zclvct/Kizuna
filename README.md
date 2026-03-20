# AI Friend - 二次元桌面助手

一个功能完整的 Live2D 二次元桌面助手，具备 AI 对话、角色设定、动态记忆、技能开关、心情驱动动作、定时任务等功能。

## 功能特性

- 🎨 **Live2D 桌面常驻** - 透明窗口，可拖拽，系统托盘
- 😊 **心情驱动动作** - LLM 根据对话内容自动选择 Live2D 动作
- 🤖 **AI 对话** - 支持多 LLM 后端 (OpenAI / Anthropic / Ollama)
- ✏️ **可定制角色设定** - 名字、性格、口癖、背景故事
- 🧠 **动态记忆成长** - LLM 在对话中学习用户信息
- 🔧 **技能开关** - 8 个工具可独立启用/禁用
- ⏰ **定时任务** - 自然语言设置，LLM 自动解析 Cron

## 技术栈

- Python 3.10+
- PySide6 (Qt6) - 跨平台 GUI
- LiteLLM - 多 LLM 后端支持
- APScheduler - 定时任务
- Pydantic - 数据验证
- PyOpenGL - Live2D 渲染

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入你的 API Key
```

### 3. 运行

```bash
python src/main.py
```

## 文档

- [功能说明书](docs/功能说明书.md) - 完整功能说明
- [技术实现细节](docs/技术实现细节.md) - 技术架构与设计
- [角色设定与记忆功能](docs/角色设定与记忆功能.md) - 角色系统设计
- [Live2D心情与动作系统](docs/Live2D心情与动作系统.md) - 动作系统设计

## 项目结构

```
aiFriend/
├── src/
│   ├── main.py              # 应用入口
│   ├── app/                 # 主窗口、托盘、菜单
│   ├── live2d/              # Live2D 渲染模块
│   ├── chat/                # 对话与 LLM 模块
│   ├── assistant/           # 助手工具集
│   ├── scheduler/           # 定时任务模块
│   └── utils/               # 工具函数
├── assets/
│   ├── live2d/              # Live2D 模型 (用户提供)
│   └── images/              # 图片资源
├── data/                    # 数据存储
└── docs/                    # 文档
```

## 许可证

MIT
