# 定时任务重构执行计划

---

## 一、架构变更概览

### 当前架构问题
1. ❌ 任务管理窗口独立，与设置分离，用户体验不连贯
2. ❌ 任务执行结果直接显示在对话窗口，不符合对话流程
3. ❌ 缺少手动测试功能
4. ❌ 任务创建方式不够直观

### 目标架构
```
┌─────────────────────────────────────────┐
│          设置窗口 (SettingsWindow)        │
│  ┌─────┬─────┬─────┬─────┬─────┬─────┐ │
│  │ LLM │Live2D│角色 │工具 │任务 │ ... │ │
│  └─────┴─────┴─────┴─────┴─────┴─────┘ │
│                                         │
│  任务页面内容:                           │
│  ┌─────────────────────────────────┐   │
│  │ 任务列表 (启用/禁用/删除/测试)    │   │
│  ├─────────────────────────────────┤   │
│  │ 执行历史日志                     │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│      对话窗口 (ChatWidget)               │
│  用户: 每天10点给我发送热点新闻          │
│  助手: 好的，已为你创建定时任务...       │
│                                         │
│  [定时触发]                             │
│  助手: 早上好！今天的新闻热点有...       │
└─────────────────────────────────────────┘
```

---

## 二、核心功能设计

### 1. 任务创建流程（LLM 驱动）

```
用户对话 → LLM 解析意图 → 生成任务配置 → 存储任务
   ↓
"每天10点发送新闻"
   ↓
LLM 返回工具调用: create_scheduled_task(
  cron="0 10 * * *",
  task_name="每日新闻推送",
  action_prompt="给用户推送今天的热点新闻"
)
```

### 2. 任务执行流程

```
定时触发 (APScheduler)
    ↓
TaskManager._execute_task()
    ↓
发送 action_prompt 到对话系统
    ↓
LLM 执行任务 (调用工具/生成内容)
    ↓
结果通过对话方式展示 (主动打开对话框)
```

### 3. 数据流设计

```python
# 任务数据模型 (增强)
class ScheduledTask:
    id: str
    task_name: str
    cron: str  # "0 10 * * *"
    action_prompt: str  # "给用户推送今天的热点新闻"
    enabled: bool
    last_run: datetime
    created_at: datetime
```

---

## 三、文件变更清单

### 需要新增的文件

| 文件路径 | 说明 |
|---------|------|
| `src/app/settings/tasks_page.py` | 设置窗口-任务页面 |
| `src/scheduler/llm_executor.py` | LLM 任务执行器 |
| `src/agent/tools/scheduler_tool.py` | 定时任务工具 (重构) |

### 需要修改的文件

| 文件路径 | 修改内容 |
|---------|---------|
| `src/app/settings/settings_window.py` | 添加任务标签页 |
| `src/scheduler/manager.py` | 修改执行逻辑，调用 LLM |
| `src/scheduler/task.py` | 简化工具定义 |
| `src/app/main_window.py` | 任务执行回调，打开对话框 |
| `src/chat/chat_widget.py` | 添加主动对话接口 |
| `src/agent/tools/__init__.py` | 导出新工具 |

### 需要删除的文件

| 文件路径 | 说明 |
|---------|------|
| `src/app/tasks_window.py` | 独立任务窗口 (功能迁移到设置页) |
| `src/app/task_edit_dialog.py` | 独立编辑对话框 (迁移到设置页) |
| `src/app/cron_builder.py` | Cron 构建器 (迁移到设置页) |
| `src/app/task_detail_dialog.py` | 任务详情对话框 (迁移到设置页) |

---

## 四、详细实施步骤

### Phase 1: UI 重构 - 任务页面 (预计 2-3 小时)

#### 1.1 创建任务页面组件
**文件**: `src/app/settings/tasks_page.py`

**功能**:
```python
class TasksSettingsPage(QWidget):
    """任务设置页面"""
    
    def _setup_ui(self):
        # 上半部分: 任务列表
        - 任务表格 (名称、Cron、状态、操作)
        - 操作按钮: 启用/禁用、删除、手动执行
        - 手动执行按钮 (用于测试)
        
        # 下半部分: 执行历史
        - 历史记录表格 (时间、任务名、结果、耗时)
        - 清理历史按钮
        
    def _load_tasks(self):
        # 加载任务列表
        
    def _load_history(self):
        # 加载执行历史
        
    def _execute_task_manually(self, task_id):
        # 手动执行任务 (用于测试)
```

**UI 设计要点**:
- 使用 QSplitter 分隔任务列表和历史记录
- 任务表格支持右键菜单 (启用/禁用/删除/执行)
- 手动执行按钮带确认提示："是否立即执行此任务？"
- 历史记录按时间倒序，最新在上

#### 1.2 集成到设置窗口
**文件**: `src/app/settings/settings_window.py`

```python
# 在 _setup_ui() 中添加
from .tasks_page import TasksSettingsPage

self.tasks_page = TasksSettingsPage()
self.tabs.addTab(self.tasks_page, "⏰ 任务")
```

---

### Phase 2: 任务创建工具重构 (预计 1-2 小时)

#### 2.1 重构工具定义
**文件**: `src/agent/tools/scheduler_tool.py`

```python
from langchain_core.tools import tool
from scheduler import get_task_manager

@tool
def create_scheduled_task(
    task_name: str,
    cron_expression: str,
    action_prompt: str
) -> str:
    """创建定时任务，在指定时间自动执行。
    
    Args:
        task_name: 任务名称，简短描述 (如 "每日新闻推送")
        cron_expression: Cron 表达式，格式 "分 时 日 月 周" 
                        (如 "0 10 * * *" 表示每天10点)
        action_prompt: 任务执行时要发送给 AI 的提示词
                      (如 "给用户推送今天的热点新闻")
    
    Returns:
        任务创建结果
    
    Examples:
        - 每天10点推送新闻: create_scheduled_task(
            "每日新闻", "0 10 * * *", "给用户推送今天的热点新闻")
        - 每周一9点提醒: create_scheduled_task(
            "周一提醒", "0 9 * * 1", "提醒用户新的一周开始了")
    """
    try:
        task_manager = get_task_manager()
        # 同步调用异步方法
        import asyncio
        task = asyncio.run(task_manager.create_task(
            task_name=task_name,
            cron=cron_expression,
            action_prompt=action_prompt
        ))
        
        return f"✅ 定时任务创建成功！\n" \
               f"任务名称: {task.task_name}\n" \
               f"执行时间: {cron_expression}\n" \
               f"任务提示: {action_prompt}"
    except Exception as e:
        return f"❌ 创建失败: {str(e)}"
```

#### 2.2 注册工具
**文件**: `src/agent/tools/__init__.py`

```python
from .scheduler_tool import create_scheduled_task

# 添加到工具列表
BUILTIN_TOOLS = [
    # ... 现有工具
    create_scheduled_task,
]
```

---

### Phase 3: LLM 任务执行器 (预计 2-3 小时)

#### 3.1 创建执行器
**文件**: `src/scheduler/llm_executor.py`

```python
class LLMTaskExecutor:
    """LLM 驱动的任务执行器"""
    
    def __init__(self, chat_widget, main_window):
        self.chat_widget = chat_widget
        self.main_window = main_window
    
    async def execute_task(self, task: ScheduledTask):
        """执行定时任务
        
        流程:
        1. 打开对话窗口
        2. 在对话中发送任务提示词
        3. LLM 自动执行并返回结果
        4. 结果显示在对话窗口
        """
        # 1. 确保对话窗口可见
        if not self.main_window._chat_visible:
            # 在主线程中显示对话窗口
            QTimer.singleShot(0, self.main_window._show_chat)
        
        # 2. 在对话中添加系统提示
        await self._add_task_prompt(task)
        
        # 3. 触发 LLM 处理
        await self._trigger_llm_response(task.action_prompt)
    
    async def _add_task_prompt(self, task: ScheduledTask):
        """在对话中添加任务提示"""
        # 添加系统消息气泡
        QTimer.singleShot(0, lambda: 
            self.chat_widget._add_message_bubble(
                f"⏰ 定时任务触发: {task.task_name}",
                is_user=False,
                is_system=True
            )
        )
        
        # 等待 UI 更新
        await asyncio.sleep(0.5)
    
    async def _trigger_llm_response(self, prompt: str):
        """触发 LLM 响应"""
        # 调用 ChatWidget 的对话接口
        # 这会自动触发 Agent 执行
        QTimer.singleShot(0, lambda:
            self.chat_widget._process_input(prompt, is_task=True)
        )
```

#### 3.2 修改任务管理器
**文件**: `src/scheduler/manager.py`

```python
class TaskManager:
    def __init__(self):
        self.storage = get_task_storage()
        self.scheduler = AsyncIOScheduler()
        self._on_task_execute: Optional[Callable] = None
        self._running = False
        self._executor: Optional[LLMTaskExecutor] = None
    
    def set_executor(self, executor: LLMTaskExecutor):
        """设置任务执行器"""
        self._executor = executor
    
    async def _execute_task(self, task_id: str):
        """执行任务"""
        task = self.storage.get(task_id)
        if not task or not task.enabled:
            return
        
        logger.info(f"执行定时任务: {task.task_name}")
        
        # 更新执行时间
        task.last_run = datetime.utcnow()
        self.storage.update(task)
        
        # 使用 LLM 执行器
        if self._executor:
            try:
                await self._executor.execute_task(task)
                # 记录成功
                self._record_execution(task, success=True)
            except Exception as e:
                logger.error(f"任务执行失败: {e}")
                self._record_execution(task, success=False, error=str(e))
```

---

### Phase 4: 主窗口集成 (预计 1-2 小时)

#### 4.1 修改主窗口
**文件**: `src/app/main_window.py`

```python
from scheduler import get_task_manager, LLMTaskExecutor

class MainWindow(QMainWindow):
    def __init__(self):
        # ... 现有代码
        
        # 初始化任务执行器
        self._setup_task_executor()
    
    def _setup_task_executor(self):
        """设置任务执行器"""
        task_manager = get_task_manager()
        
        # 创建执行器
        executor = LLMTaskExecutor(
            chat_widget=self.chat_bubble.chat_widget,
            main_window=self
        )
        
        task_manager.set_executor(executor)
        logger.info("任务执行器已初始化")
```

#### 4.2 删除独立任务窗口相关代码
**文件**: `src/app/main_window.py`

```python
# 删除以下内容:
# - from app.tasks_window import TasksWindow
# - self.tasks_window = TasksWindow()
# - 右键菜单中的 "查看定时任务" 选项 (改为打开设置-任务页)
```

---

### Phase 5: ChatWidget 增强 (预计 1 小时)

#### 5.1 添加任务输入接口
**文件**: `src/chat/chat_widget.py`

```python
class ChatWidget(QFrame):
    def _process_input(self, text: str, is_task: bool = False):
        """处理输入
        
        Args:
            text: 输入文本
            is_task: 是否为任务触发 (区别于用户输入)
        """
        if not is_task:
            # 用户输入: 显示用户消息
            self._add_message_bubble(text, is_user=True)
        
        # 触发 LLM 处理
        asyncio.create_task(self._handle_message(text))
```

---

## 五、技术实现要点

### 1. 线程安全
```python
# APScheduler 在后台线程执行
# UI 更新必须在主线程

# ❌ 错误做法
self.chat_widget._add_message_bubble(...)

# ✅ 正确做法
QTimer.singleShot(0, lambda: 
    self.chat_widget._add_message_bubble(...)
)
```

### 2. 异步任务管理
```python
# 在主窗口中启动任务管理器
async def start_task_manager():
    task_manager = get_task_manager()
    await task_manager.start()
    
    # 在单独的事件循环中运行
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_task_manager())
```

### 3. 任务执行的对话上下文
```python
# 任务触发时，需要在对话历史中添加上下文
# 方式 1: 直接添加到记忆
memory = get_langchain_memory()
memory.chat_memory.add_ai_message(
    f"[系统] 定时任务 '{task.task_name}' 触发"
)

# 方式 2: 作为系统提示传入
await agent.chat(
    message=task.action_prompt,
    system_context=f"定时任务 {task.task_name} 触发"
)
```

---

## 六、测试计划

### 6.1 功能测试
```
□ 任务创建测试
  - 对话创建任务: "每天10点提醒我开会"
  - 验证任务是否正确创建
  - 验证 Cron 表达式是否正确

□ 任务执行测试
  - 在设置页面手动执行任务
  - 验证对话窗口是否自动打开
  - 验证 LLM 是否收到提示词
  - 验证结果是否在对话中显示

□ 定时触发测试
  - 创建 1 分钟后触发的任务
  - 等待触发
  - 验证执行结果

□ UI 交互测试
  - 在设置页面查看任务列表
  - 启用/禁用任务
  - 删除任务
  - 查看执行历史
```

### 6.2 边界情况测试
```
□ 对话窗口关闭时的行为
  - 任务触发时窗口关闭 → 应自动打开

□ 多任务同时触发
  - 验证任务队列处理

□ 任务执行失败
  - 验证错误记录
  - 验证历史记录
```

---

## 七、实施时间估算

| Phase | 任务 | 预计时间 | 状态 |
|-------|------|---------|------|
| Phase 1 | UI 重构 - 任务页面 | 2-3 小时 | ⏳ 进行中 |
| Phase 2 | 任务创建工具重构 | 1-2 小时 | ⏸️ 待开始 |
| Phase 3 | LLM 任务执行器 | 2-3 小时 | ⏸️ 待开始 |
| Phase 4 | 主窗口集成 | 1-2 小时 | ⏸️ 待开始 |
| Phase 5 | ChatWidget 增强 | 1 小时 | ⏸️ 待开始 |
| 测试 | 功能测试 & 调试 | 2 小时 | ⏸️ 待开始 |
| **总计** | | **9-13 小时** | |

---

## 八、后续优化方向

1. **任务模板**: 提供常用任务模板 (每日新闻、天气提醒等)
2. **任务分组**: 按类型分组管理任务
3. **任务依赖**: 支持任务依赖关系 (任务A完成后执行任务B)
4. **可视化调度**: 时间轴显示任务分布
5. **任务失败重试**: 自动重试失败的任务
6. **任务通知**: 任务执行前后发送桌面通知

---

## 九、实施日志

### [日期] Phase 1 完成
- ✅ 创建任务页面组件
- ✅ 集成到设置窗口
- ✅ 实现任务列表显示
- ✅ 实现执行历史显示
- ✅ 实现手动执行功能

### [日期] Phase 2 完成
- ...

---

**创建时间**: 2026-03-25  
**最后更新**: 2026-03-25  
**当前进度**: Phase 1 进行中
