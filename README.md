# AI Friend - 二次元桌面助手

一个功能完整的 Live2D 二次元桌面助手，具备 AI 对话、角色设定、动态记忆、技能开关、心情驱动动作、定时任务、任务编辑、执行历史等功能。

## 功能特性

### 核心功能
- 🎨 **Live2D 桌面常驻** - 透明窗口，可拖拽，系统托盘
- 😊 **心情驱动动作** - LLM 根据对话内容自动选择 Live2D 动作
- 🤖 **AI 对话** - 支持多 LLM 后端 (OpenAI / Anthropic / Ollama)
- ✏️ **可定制角色设定** - 名字、性格、口癖、背景故事
- 🧠 **动态记忆成长** - LLM 在对话中学习用户信息
- 🔧 **技能开关** - 多个工具可独立启用/禁用
- ⏰ **定时任务** - 自然语言设置，LLM 自动解析 Cron

### Phase 7 新增功能
- 🖥️ **完整设置界面** - 6 个标签页，全面配置选项
  - LLM 配置（提供商、模型、API Key、Base URL）
  - Live2D 配置（模型路径、缩放、动作设置）
  - 角色设定（基本信息、性格、背景故事、喜好）
  - 技能管理（8+ 个工具，可独立开关）
  - 通用设置（开机自启、窗口置顶、音效、日志级别）
  - 界面设置（Live2D 渲染方式、窗口透明度、动画效果）
- 🌐 **Live2D WebEngine 备选方案** - 兼容性更强的渲染方式
- 🛠️ **错误处理与日志完善** - 更好的异常处理和日志记录
- 📊 **任务执行历史** - 查看任务执行记录和统计信息
- ✏️ **任务编辑功能** - 修改任务配置和 Cron 表达式
- 🔧 **Cron 表达式构建器** - 可视化构建 Cron 表达式（每天/每周/每月/每小时/自定义）
- 🎯 **任务详情查看** - 查看任务完整信息和执行历史
- ⚡ **手动触发任务** - 立即执行任务进行测试

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

### 核心文档
- [功能说明书](docs/功能说明书.md) - 完整功能说明
- [技术实现细节](docs/技术实现细节.md) - 技术架构与设计
- [角色设定与记忆功能](docs/角色设定与记忆功能.md) - 角色系统设计
- [Live2D心情与动作系统](docs/Live2D心情与动作系统.md) - 动作系统设计

### 开发文档
- [Phase 1 完成报告](docs/phase1_completion.md) - Live2D 桌面常驻窗口
- [Phase 2 完成报告](docs/phase2_completion.md) - 对话与角色设定
- [Phase 3 完成报告](docs/phase3_completion.md) - 工具系统
- [Phase 4 完成报告](docs/phase4_completion.md) - 心情驱动动作
- [Phase 5 完成报告](docs/phase5_completion.md) - 定时任务
- [Phase 6 完成报告](docs/phase6_completion.md) - 定时任务完善（编辑、历史、详情）
- [Phase 7 完成报告](docs/phase7_completion.md) - 整合与完善
- [Agent Team Prompt](docs/agent_team_prompt.md) - 开发规范

## 项目结构

```
aiFriend/
├── src/
│   ├── main.py              # 应用入口
│   ├── app/                 # 主窗口、托盘、菜单
│   │   ├── main_window.py          # 主窗口（整合 Live2D + 对话）
│   │   ├── settings_window.py      # 设置窗口（6 个标签页）
│   │   ├── tasks_window.py         # 定时任务窗口
│   │   ├── task_edit_dialog.py     # 任务编辑对话框
│   │   ├── task_detail_dialog.py   # 任务详情对话框
│   │   ├── cron_builder.py         # Cron 表达式构建器
│   │   ├── context_menu.py         # 右键菜单
│   │   └── chat_widget.py          # 对话窗口组件
│   ├── live2d/              # Live2D 渲染模块
│   │   ├── widget.py               # Live2D 控件（Native）
│   │   ├── web_widget.py           # Live2D 控件（WebEngine）
│   │   ├── model_manager.py        # 模型管理器
│   │   ├── motion_controller.py    # 动作控制器
│   │   └── cubism_loader.py        # Cubism SDK 加载器
│   ├── chat/                # 对话与 LLM 模块
│   │   ├── chat_widget.py          # 对话窗口
│   │   ├── llm_client.py           # LLM 客户端
│   │   ├── conversation_manager.py # 对话管理器
│   │   ├── message_bubble.py       # 消息气泡
│   │   └── thinking_indicator.py   # 思考指示器
│   ├── assistant/           # 助手工具集
│   │   ├── tool_registry.py        # 工具注册表
│   │   ├── tools/                 # 工具实现
│   │   │   ├── time_tool.py
│   │   │   ├── weather_tool.py
│   │   │   ├── search_tool.py
│   │   │   ├── memory_tool.py
│   │   │   ├── motion_tool.py
│   │   │   └── schedule_tool.py
│   │   └── prompts/               # 提示词模板
│   ├── scheduler/           # 定时任务模块
│   │   ├── manager.py              # 任务管理器
│   │   ├── task.py                 # 任务模型
│   │   ├── storage.py              # 任务存储
│   │   ├── parser.py               # Cron 解析器
│   │   └── task_history.py         # 执行历史
│   ├── utils/               # 工具函数
│   │   ├── config.py              # 配置管理
│   │   ├── character.py           # 角色管理
│   │   ├── logger.py              # 日志工具
│   │   └── constants.py           # 常量定义
│   └── voice/               # 语音交互模块（Phase 8 预留）
├── assets/
│   ├── live2d/              # Live2D 模型 (用户提供)
│   │   └── biaoqiang/        # 示例模型
│   └── images/              # 图片资源
├── data/                    # 数据存储
│   ├── config.json          # 配置文件
│   ├── character.json       # 角色设定
│   ├── conversation.json    # 对话历史
│   ├── skills.json          # 技能配置
│   ├── tasks.json           # 定时任务
│   ├── task_history.json    # 执行历史
│   └── motion_config.json   # 动作配置
├── docs/                    # 文档
├── requirements.txt         # Python 依赖
├── run.py                   # 简化运行入口
└── README.md                # 项目说明
```

## 使用指南

### 首次运行

1. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

2. **配置环境变量**
   ```bash
   cp .env.example .env
   # 编辑 .env，填入你的 API Key
   ```

3. **准备 Live2D 模型**
   - 将 Live2D 模型放入 `assets/live2d/your_model/` 目录
   - 在设置中配置模型路径

4. **运行应用**
   ```bash
   python src/main.py
   ```

### 基本操作

- **拖拽窗口**：鼠标左键拖拽 Live2D 角色
- **切换对话窗口**：点击 💬 按钮（右键菜单也可以）
- **打开设置**：右键点击角色 → 设置
- **查看定时任务**：右键点击角色 → 查看定时任务
- **退出应用**：右键点击角色 → 退出（或系统托盘退出）

### LLM 配置

支持多种 LLM 后端：

#### OpenAI / Azure OpenAI
```bash
LLM_PROVIDER=openai
LLM_MODEL=gpt-4
OPENAI_API_KEY=your-api-key
OPENAI_BASE_URL=https://api.openai.com/v1  # 可选
```

#### Anthropic Claude
```bash
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-sonnet-20240229
ANTHROPIC_API_KEY=your-api-key
```

#### Ollama (本地)
```bash
LLM_PROVIDER=ollama
LLM_MODEL=llama2
OLLAMA_BASE_URL=http://localhost:11434
```

### 定时任务

#### 创建任务
1. 打开定时任务窗口
2. 点击"创建任务"
3. 填写任务名称和动作提示
4. 选择 Cron 预设或使用 Cron 构建器
5. 选择 Live2D 动作（可选）

#### Cron 表达式示例
- `0 8 * * *` - 每天 8:00
- `0 9 * * 1` - 每周一 9:00
- `0 */2 * * *` - 每 2 小时
- `30 18 * * 1-5` - 工作日 18:30

#### 任务操作
- **启用/禁用**：点击"启"或"停"按钮
- **编辑**：点击"编辑"按钮修改任务
- **立即执行**：点击"运行"按钮手动触发
- **查看详情**：双击任务或右键菜单
- **删除**：点击"删除"按钮

### 技能管理

在设置的"技能"标签页中，可以：

- 查看所有可用工具
- 启用/禁用单个技能
- 全选/反选技能

可用的工具包括：
- 🕐 时间工具
- 🌤️ 天气工具
- 🔍 搜索工具
- 🧠 记忆工具
- 🎭 动作工具
- 📋 定时任务工具

### 角色设定

在设置的"角色设定"标签页中，可以自定义：

- **基本信息**：名字、性别、年龄、生日
- **性格设定**：性格、口癖/说话风格
- **关系设定**：与用户的关系、用户昵称
- **背景故事**：角色的背景故事
- **喜好设定**：喜欢和讨厌的事物

### Live2D 配置

#### 渲染方式
- **Native（推荐）**：性能好，但对 Live2D 版本有要求
- **WebEngine**：兼容性强，但占用资源较多

如果遇到渲染问题，可以在设置的"界面"标签页中切换渲染方式。

#### 动作配置
在设置的"Live2D"标签页中，可以：

- 配置心情动作映射
- 配置意图动作映射
- 配置空闲动作
- 启用/禁用心情驱动动作
- 启用/禁用空闲动作
- 设置空闲动作间隔

### 界面设置

在设置的"界面"标签页中，可以：

- 选择 Live2D 渲染方式
- 调整窗口透明度
- 启用/禁用窗口动画

### 日志和调试

#### 查看日志
日志文件位于 `data/app.log`

#### 调整日志级别
在设置的"通用"标签页中，可以设置日志级别：
- DEBUG：详细调试信息
- INFO：一般信息（默认）
- WARNING：警告信息
- ERROR：错误信息

#### 常见问题

**问题：Live2D 模型无法加载**
- 检查模型路径是否正确
- 尝试切换到 WebEngine 渲染方式
- 查看日志文件了解详细错误信息

**问题：LLM 调用失败**
- 检查 API Key 是否正确
- 检查网络连接
- 查看日志文件了解详细错误信息

**问题：定时任务不执行**
- 检查任务是否启用
- 检查 Cron 表达式是否正确
- 查看任务详情中的执行历史

**问题：动作不播放**
- 检查动作配置是否正确
- 检查动作文件是否存在
- 在设置中测试动作

## 开发指南

### 添加新工具

1. 在 `src/assistant/tools/` 创建新工具文件
2. 实现工具类，继承 `BaseTool`
3. 在 `src/assistant/tool_registry.py` 中注册
4. 在设置中添加开关（可选）

### 添加新的 Live2D 动作

1. 在 Live2D 模型目录中添加动作文件
2. 在 `data/motion_config.json` 中配置动作映射
3. 在设置的"Live2D"标签页中测试

### 自定义角色

编辑 `data/character.json` 文件，或使用设置窗口的"角色设定"标签页。

## 技术支持

- 查看 [文档目录](docs/) 获取更多详细信息
- 查看 [Phase 完成报告](docs/) 了解开发进度
- 查看 [技术实现细节](docs/技术实现细节.md) 了解架构设计

## 许可证

MIT

## 许可证

MIT
