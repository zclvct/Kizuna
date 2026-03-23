# AI Friend 项目开发 - Agent Team 任务说明

## 项目概述

**项目名称**: AI Friend - 二次元桌面助手

**目标**: 创建一个功能完整的 Live2D 二次元桌面助手，具备 AI 对话、角色设定、动态记忆、技能开关、心情驱动动作、定时任务等功能。

**技术栈**:
- 语言: Python 3.10+
- GUI 框架: PySide6 (Qt6)
- LLM: LiteLLM (支持 OpenAI / Anthropic / Ollama)
- 定时任务: APScheduler
- 数据验证: Pydantic
- Live2D: OpenGL + Cubism Core (备选: WebEngineView)

---

## 项目文档

请先仔细阅读以下文档，了解需求细节：
- `docs/功能说明书.md` - 完整功能说明
- `docs/技术实现细节.md` - 技术实现细节
- `docs/角色设定与记忆功能.md` - 角色系统设计
- `docs/Live2D心情与动作系统.md` - 动作系统设计

---

## 目录结构

```
aiFriend/
├── src/
│   ├── main.py                      # 应用入口
│   ├── app/
│   │   ├── main_window.py           # 主窗口
│   │   ├── tray_icon.py             # 系统托盘
│   │   ├── settings_window.py       # 设置窗口
│   │   ├── context_menu.py          # 右键菜单
│   │   └── motion_config_window.py  # 动作配置窗口 (可选)
│   ├── live2d/
│   │   ├── __init__.py
│   │   ├── widget.py                # Live2D Qt 控件
│   │   ├── renderer.py              # OpenGL 渲染器
│   │   ├── model.py                 # 模型管理
│   │   ├── motion_controller.py    # 动作控制器 (含心情状态)
│   │   └── cubism_bindings.py      # Cubism Core 绑定 (可选)
│   ├── chat/
│   │   ├── __init__.py
│   │   ├── llm_client.py            # LLM 客户端
│   │   ├── conversation_manager.py  # 对话管理
│   │   ├── chat_widget.py           # 对话窗口
│   │   └── message_bubble.py       # 消息气泡
│   ├── assistant/
│   │   ├── __init__.py
│   │   ├── tool_registry.py         # 工具注册
│   │   ├── function_calling.py      # Function Calling 处理
│   │   └── tools/
│   │       ├── __init__.py
│   │       ├── time_tool.py
│   │       ├── weather_tool.py
│   │       ├── todo_tool.py
│   │       ├── clipboard_tool.py
│   │       ├── system_tool.py
│   │       ├── launcher_tool.py
│   │       ├── persona_tool.py      # 角色设定编辑工具
│   │       └── motion_tool.py       # 动作控制工具
│   ├── scheduler/
│   │   ├── __init__.py
│   │   ├── manager.py               # 任务管理器
│   │   ├── parser.py                # LLM 任务解析器
│   │   ├── task.py                  # 任务数据模型
│   │   └── storage.py               # 任务持久化
│   └── utils/
│       ├── __init__.py
│       ├── config.py                # 配置管理
│       ├── character.py             # 角色设定管理
│       ├── logger.py                # 日志
│       └── constants.py             # 常量
├── assets/
│   ├── live2d/
│   │   └── README.md
│   └── images/
├── data/
├── docs/
├── requirements.txt
├── .env.example
└── README.md
```

---

## 开发阶段规划

### Phase 1: 项目基础 (MVP)
**目标**: 搭建基础框架，能跑起来

1. 创建项目目录结构
2. 编写 requirements.txt 和 .env.example
3. 实现 utils 模块 (config, logger, constants, character)
4. 实现基础 PySide6 主窗口 (无边框、透明、可拖拽)
5. 实现系统托盘和右键菜单
6. 创建简单的 Live2D widget (占位，后续再完善)
7. 实现基础对话窗口 UI

### Phase 2: 对话与 LLM
**目标**: 实现完整的对话功能

1. 实现 LLM 客户端 (LiteLLM 封装)
2. 实现对话管理 (历史记录、持久化)
3. 实现对话窗口 (消息气泡、输入框、发送)
4. 整合角色设定到 System Prompt
5. 实现流式输出显示

### Phase 3: 角色设定与记忆
**目标**: 实现可定制的角色系统

1. 完善 CharacterPersona 模型
2. 实现 CharacterManager
3. 实现 persona_edit tool (Function Calling)
4. 实现设置窗口的"角色设定"标签页
5. 实现第一次启动引导对话

### Phase 4: 技能系统与助手工具
**目标**: 实现工具注册和调用

1. 实现 ToolRegistry
2. 逐个实现工具 (time, weather, todo, clipboard, system, launcher)
3. 实现 Function Calling 处理流程
4. 实现设置窗口的"技能"标签页
5. 整合技能开关到工具调用

### Phase 5: Live2D 心情与动作
**目标**: 实现动作系统

1. 实现 MotionController (含心情状态)
2. 实现 motions.json 配置加载
3. 实现 motion_tool (Function Calling)
4. 整合动作播放到对话流程
5. 实现空闲动作定时器
6. 实现设置窗口的动作配置

### Phase 6: 定时任务
**目标**: 实现 LLM 驱动的定时任务

1. 实现 ScheduledTask 模型
2. 实现 TaskManager (APScheduler 封装)
3. 实现任务解析器 (LLM 驱动)
4. 实现任务持久化
5. 实现任务执行回调 (LLM + 动作)

### Phase 7: 整合与完善
**目标**: 所有模块整合，完善 UI

1. 主窗口整合 (Live2D + 对话)
2. 实现完整的设置窗口 (5 个标签页)
3. Live2D 渲染完善
4. 测试完整流程
5. 错误处理与日志完善
6. 编写 README

---

## 编码规范

### 代码风格
- 使用 type hints (Python 3.10+ 语法)
- 使用 Pydantic 进行数据验证
- 异步代码使用 async/await
- 日志使用 logging 模块

### 配置管理
- 所有配置通过 `utils.config` 模块管理
- 敏感信息从环境变量读取
- 默认配置有合理的默认值

### 错误处理
- 所有异步操作都有 try/except
- 用户友好的错误提示
- 详细的错误日志

---

## 数据模型示例

### CharacterPersona (角色设定)
```python
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime

class CharacterPersona(BaseModel):
    name: str = ""
    gender: str = ""
    age: str = ""
    birthday: str = ""
    personality: str = ""
    speech_style: str = ""
    first_person: str = "我"
    second_person: str = "你"
    user_nickname: str = ""
    relationship: str = "朋友"
    background: str = ""
    likes: List[str] = Field(default_factory=list)
    dislikes: List[str] = Field(default_factory=list)
    memories: List[Dict] = Field(default_factory=list)
    learned_facts: Dict[str, str] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def to_system_prompt(self) -> str:
        # 转换为 System Prompt
        pass
```

### ScheduledTask (定时任务)
```python
class ScheduledTask(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    task_name: str
    cron: str
    action_prompt: str
    motion_id: Optional[str] = None
    enabled: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
```

---

## Function Calling Tools

### 1. edit_persona
修改角色设定、记忆、学到的信息。

### 2. play_motion
播放 Live2D 动作/表情。

### 3. create_scheduled_task
创建定时任务。

### 4-9. 各种工具 (time, weather, todo 等)

---

## 注意事项

1. **从简到繁**: 先实现 MVP，再逐步添加功能
2. **可运行优先**: 每个阶段结束时都应该有一个可运行的版本
3. **备选方案**: Live2D 原生渲染复杂时，先用 WebEngineView 嵌入 Web 版 Live2D
4. **持久化**: 所有数据都要保存到 JSON 文件
5. **配置分离**: 用户配置和代码分离

---

## 团队协作

如果使用多个 agent，请按模块分工：
- **Agent 1**: 项目基础 + utils + 主窗口
- **Agent 2**: 对话系统 + LLM 客户端
- **Agent 3**: 角色设定 + 技能系统
- **Agent 4**: Live2D + 动作系统
- **Agent 5**: 定时任务 + 整合测试

---

## 验收标准

- [ ] 项目能正常启动，显示主窗口
- [ ] Live2D 角色显示 (或占位)
- [ ] 可以与 LLM 对话
- [ ] 角色设定可以编辑和保存
- [ ] LLM 可以在对话中学习新信息
- [ ] 心情驱动的动作正常播放
- [ ] 可以通过对话设置定时任务
- [ ] 定时任务正常触发
- [ ] 所有设置项都能正常保存

祝开发顺利！
