# LangChain 重构计划

## 一、重构目标

将当前的 LiteLLM + 自定义 Orchestrator 架构迁移到 LangChain 框架，实现：
1. **统一的模型调用接口** - 使用 LangChain 的 ChatModel
2. **自动化的工具调用** - 使用 LangChain Agent 自动处理 function calling
3. **标准化记忆管理** - 使用 LangChain Memory
4. **更好的模型兼容性** - 支持更多 LLM 提供商

## 二、技术选型

### 核心依赖

```txt
# LangChain 核心
langchain>=0.3.0
langchain-core>=0.3.0
langchain-community>=0.3.0

# 模型支持
langchain-openai>=0.2.0      # OpenAI 兼容 API
langchain-ollama>=0.2.0      # Ollama 本地模型

# 工具支持
langchain-tools>=0.1.0       # 内置工具

# 数据验证
pydantic>=2.5.0

# 现有依赖保留
PySide6>=6.6.0
live2d-py>=0.6.0
PyOpenGL>=3.1.7
requests>=2.31.0
psutil>=5.9.6
pyperclip>=1.8.2
apscheduler>=3.10.4
```

### 架构对比

| 当前架构 | LangChain 架构 |
|---------|---------------|
| `LLMClient` (LiteLLM) | `langchain_openai.ChatOpenAI` |
| `AgentOrchestrator` (手动编排) | `langchain.agents.AgentExecutor` |
| `ToolManager` (自定义) | `langchain_core.tools.StructuredTool` |
| `MemoryManager` (自定义) | `langchain.memory.*` |
| `PromptManager` (自定义) | `langchain_core.prompts.*` |

## 三、重构步骤

### 阶段一：基础设施重构 ✅ 已完成

#### 1.1 更新依赖
- [x] 更新 `requirements.txt` - 添加 LangChain 核心依赖
- [x] 创建 LangChain 配置模块

#### 1.2 创建新的模型配置
- [x] 创建 `src/agent/models/__init__.py`
- [x] 创建 `src/agent/models/config.py` - LLM 配置类（支持多提供商）
- [x] 创建 `src/agent/models/factory.py` - 模型工厂（支持 OpenAI/Ollama/DeepSeek）

#### 1.3 统一配置管理
- [x] 创建 `src/agent/config.py` - 统一配置类
- [x] 使用 Pydantic BaseModel 管理所有配置
- [x] 整合工具配置（从 tools_config.py 兼容加载）

---

### 阶段二：工具迁移 ✅ 已完成

#### 2.1 工具基类定义
- [x] 创建 `src/agent/tools/base.py` - LangChain 工具基类

#### 2.2 迁移现有工具
- [x] 创建 `src/agent/tools/langchain_tools.py` - 统一转换所有工具为 LangChain StructuredTool
- [x] 迁移 `motion_tool.py` → LangChain Tool
- [x] 迁移 `persona_tool.py` → LangChain Tool
- [x] 迁移 `time_tool.py` → LangChain Tool
- [x] 迁移 `weather_tool.py` → LangChain Tool
- [x] 迁移 `todo_tool.py` → LangChain Tool
- [x] 迁移 `clipboard_tool.py` → LangChain Tool
- [x] 迁移 `system_tool.py` → LangChain Tool
- [x] 迁移 `launcher_tool.py` → LangChain Tool

#### 2.3 创建工具注册器
- [x] 创建 `src/agent/tools/registry.py` - 单例模式的工具注册器

---

### 阶段三：智能体重构 ✅ 已完成

#### 3.1 创建 LangChain Agent
- [x] 创建 `src/agent/agent.py` - 基于 LangChain AgentExecutor

#### 3.2 流式输出支持
- [x] 实现 `astream_events` 流式输出

---

### 阶段四：记忆管理迁移 ✅ 已完成

#### 4.1 使用 LangChain Memory
- [x] 创建 `src/agent/memory.py` - 与现有 MemoryManager 兼容

#### 4.2 长期记忆（可选）
- [x] 集成现有长期记忆系统（通过 MemoryManager）

---

### 阶段五：提示词管理 ✅ 已完成

#### 5.1 使用 LangChain PromptTemplate
- [x] 创建 `src/agent/prompts.py` - 复用现有 PromptManager

---

### 阶段六：整合与测试 ✅ 已完成

#### 6.1 创建新的入口
- [x] 创建 `src/agent/core.py` - 统一入口 AIFriendCore

#### 6.2 更新 UI 层
- [x] 更新 `chat_widget.py` 使用新的 `AIFriendCore`
- [x] 更新 `main.py` 使用 LangChain 初始化
- [x] 保持 Live2D 集成不变

#### 6.3 测试
- [ ] 测试 Ollama 模型调用
- [ ] 测试工具调用
- [ ] 测试流式输出
- [ ] 测试 Live2D 动作触发

---

## 四、文件变更清单

### 新增文件

```
src/agent/
├── models/
│   ├── __init__.py
│   ├── config.py          # LLM 配置（Pydantic）
│   └── factory.py         # 模型工厂（支持 OpenAI/Ollama/DeepSeek）
├── tools/
│   ├── base.py            # LangChain 工具基类
│   ├── langchain_tools.py # 工具转换为 StructuredTool
│   └── registry.py        # 工具注册器（单例）
├── config.py              # 统一配置类
├── memory.py              # LangChain Memory 封装
├── prompts.py             # LangChain PromptTemplate
├── agent.py               # AIFriendAgent 核心类
└── core.py                # AIFriendCore 统一入口
```

### 保留文件（向后兼容）

```
src/agent/
├── llm_client.py          # 保留，旧代码可能使用
├── orchestrator.py        # 保留，旧代码可能使用
├── tool_manager.py        # 保留，LangChain 工具内部使用
├── memory_manager.py      # 保留，LangChain Memory 内部使用
├── prompt_manager.py      # 保留，LangChain Prompts 内部使用
└── skill_manager.py       # 保留，技能触发功能

src/utils/
└── tools_config.py        # 保留，工具启用状态管理
```

### 修改文件

```
requirements.txt           # 添加 LangChain 依赖，移除 litellm
src/chat/chat_widget.py    # 使用 AIFriendCore 替代 Orchestrator
src/main.py               # 使用 LangChain 初始化
src/agent/__init__.py     # 导出新模块
src/agent/tools/__init__.py # 导出 LangChain 工具
```

---

## 五、风险与应对

### 风险 1：Ollama 兼容性
- **问题**：`langchain-ollama` 对工具调用支持可能不完善
- **应对**：先测试 `langchain-ollama` 的工具调用，如有问题使用 `langchain-openai` + Ollama OpenAI 兼容 API

### 风险 2：流式输出中断
- **问题**：LangChain 流式输出与工具调用的结合可能有边界情况
- **应对**：使用 `astream_events` API，它能正确处理工具调用和流式输出

### 风险 3：现有功能丢失
- **问题**：迁移过程中可能丢失某些边缘功能
- **应对**：分阶段迁移，每阶段完成后运行测试，保留旧代码直到新代码稳定

---

## 六、回滚方案

如果重构过程中遇到不可解决的问题：

1. **保留旧代码**：不要删除 `llm_client.py` 和 `orchestrator.py`，先重命名为 `*.py.bak`
2. **配置回滚**：`requirements.txt` 保留 LiteLLM 依赖
3. **功能开关**：在配置中添加 `use_langchain: false` 开关

---

## 七、执行顺序

```
阶段一（基础设施）→ 阶段二（工具）→ 阶段三（智能体）→ 阶段四（记忆）→ 阶段五（提示词）→ 阶段六（整合测试）
```

每个阶段完成后提交代码，确保可回滚。

---

## 八、预期收益

1. **代码量减少**：~500 行 → ~200 行（Agent 编排逻辑）
2. **维护成本降低**：使用成熟的框架，减少自定义代码
3. **扩展性增强**：轻松添加新的 LLM 提供商和工具
4. **工具调用稳定性**：LangChain 自动处理 function calling，无需手动解析 JSON
5. **流式输出优化**：统一的流式处理，用户体验更好
