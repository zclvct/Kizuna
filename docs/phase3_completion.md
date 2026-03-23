# Phase 3 完成报告 - 角色设定与记忆功能

## 完成时间
2024-03-20

## 实现概述
Phase 3 专注于实现角色设定与记忆功能，让 AI 助手能够学习用户信息、记住重要事件，并提供第一次启动的引导对话。

---

## 完成的功能

### 1. CharacterPersona 模型 ✓
**文件**: `src/utils/character.py`

**实现内容**:
- 完整的角色设定数据模型
- 包含基础信息（名字、性别、年龄、生日）
- 性格设定（性格描述、说话风格、自称、称呼）
- 关系设定（关系、用户昵称）
- 背景故事
- 喜好设定（喜欢/讨厌）
- 动态记忆（memories 列表）
- 学到的事实（learned_facts 字典）

**关键方法**:
- `to_system_prompt()`: 自动生成 System Prompt
- `is_first_run()`: 检测是否第一次运行
- `CharacterState`: 角色心情状态管理

---

### 2. CharacterManager ✓
**文件**: `src/utils/character.py`

**实现内容**:
- 角色设定持久化（保存到 `data/character.json`）
- 记忆管理（添加、自动限制数量）
- 事实管理（设置、删除）
- 默认角色创建
- 随机问候语生成

**关键方法**:
- `save()`: 保存设定到文件
- `add_memory()`: 添加重要记忆
- `set_fact()`: 设置学到的用户信息
- `get_random_greeting()`: 获取第一次启动的问候语

---

### 3. persona_edit Tool (Function Calling) ✓
**文件**: `src/assistant/tools/persona_tool.py`

**实现内容**:
- 支持多种操作类型：
  - `set_name`: 设置角色名字
  - `set_field`: 设置任意字段
  - `add_memory`: 添加记忆
  - `add_fact`: 记录事实
  - `remove_memory`: 删除记忆
  - `remove_fact`: 删除事实
- 敏感字段确认机制（第一次启动除外）
- 自动记录重要事件到记忆

**工具定义**:
```python
edit_persona(
    action: str,  # 操作类型
    field: Optional[str],  # 字段名
    value: Optional[str],  # 字段值
    content: Optional[str],  # 记忆内容
    key: Optional[str],  # 事实键名
    confirm: bool = False  # 是否已确认
)
```

---

### 4. 第一次启动引导对话 ✓
**文件**:
- `src/chat/chat_widget.py`
- `src/chat/llm_client.py`

**实现内容**:

#### ChatWidget 修改:
- 添加 `_check_first_run()` 方法
- 第一次启动时显示随机问候语
- 主窗口自动显示对话窗口

#### System Prompt 增强:
- 第一次启动时，特殊指令引导 LLM：
  1. 询问用户姓名
  2. 询问如何称呼角色
  3. 询问角色与用户的关系
  4. 使用 edit_persona 工具保存信息
  5. 友好结束引导

**对话流程示例**:
```
用户: (第一次启动)

角色: 你好，初次见面！我还没有名字，能给我起个名字吗？

用户: 以后你就叫小秘

角色: (调用 edit_persona(action="set_name", value="小秘"))
      好的，主人！以后我就是小秘了~的说 ♪
      对了，主人怎么称呼呢？

用户: 叫我小明就好

角色: (调用 edit_persona(action="set_field", field="second_person", value="小明"))
      (调用 edit_persona(action="add_fact", key="用户姓名", value="小明"))
      好的，小明！很高兴认识你 😊
```

---

### 5. 设置窗口 - 角色设定标签页 ✓
**文件**: `src/app/settings_window.py`

**实现内容**:
- **基础信息**: 名字、性别、年龄、生日
- **性格设定**: 性格、口癖、自称、称呼
- **关系设定**: 关系、用户昵称
- **背景故事**: 多行文本编辑
- **喜好设定**: 喜欢/讨厌（逗号分隔）

**功能**:
- 自动加载角色设定
- 保存修改到 character.json
- 与主窗口实时同步

---

## 技术亮点

### 1. 动态 System Prompt 生成
```python
def _build_system_prompt(self) -> str:
    base = persona.to_system_prompt()
    mood_info = f"\n\n你当前的心情是：{state.current_mood}"

    if persona.is_first_run():
        # 第一次启动的特殊指令
        first_run_instruction = """
【第一次启动引导】
你是第一次与用户见面...
"""
        return base + mood_info + first_run_instruction
    else:
        # 正常对话的指令
        tool_instruction = """
你可以使用以下工具...
"""
        return base + mood_info + tool_instruction
```

### 2. 记忆管理策略
- 自动限制记忆数量（最多 100 条）
- 按时间顺序存储
- 支持删除特定记忆
- 事实信息使用键值对存储，便于查询

### 3. 第一次启动检测
```python
def is_first_run(self) -> bool:
    """是否是第一次运行（没有名字）"""
    return not self.name
```

---

## 数据持久化

### character.json 格式
```json
{
  "name": "小秘",
  "gender": "女",
  "age": "17",
  "birthday": "2007-03-20",
  "personality": "活泼开朗，有点小傲娇",
  "speech_style": "句尾加『~的说』",
  "first_person": "人家",
  "second_person": "主人",
  "user_nickname": "亲爱的",
  "relationship": "专属助手",
  "background": "从二次元世界来的助手",
  "likes": ["主人", "咖啡", "动漫"],
  "dislikes": ["蟑螂", "苦味的东西"],
  "memories": [
    {
      "content": "主人给我起了名字叫小秘",
      "timestamp": "2024-03-20T10:00:00Z"
    }
  ],
  "learned_facts": {
    "用户姓名": "小明",
    "用户喜好": "咖啡",
    "用户作息": "一般晚上12点睡觉"
  },
  "created_at": "2024-03-20T10:00:00Z",
  "updated_at": "2024-03-20T10:30:00Z"
}
```

---

## 与其他模块的集成

### 1. 与 LLM 客户端集成
- 自动生成 System Prompt
- 第一次启动的特殊指令
- 工具调用支持

### 2. 与 Function Calling 集成
- edit_persona 工具已注册
- 支持异步执行
- 敏感字段确认机制

### 3. 与设置窗口集成
- 角色设定标签页完整实现
- 实时保存和加载

### 4. 与主窗口集成
- 第一次启动自动显示对话窗口
- 自动触发引导对话

---

## 测试建议

### 测试场景 1: 第一次启动
1. 删除 `data/character.json`
2. 启动应用
3. 对话窗口应自动显示
4. 角色应主动问候并询问名字
5. 完成引导流程后，检查 character.json

### 测试场景 2: 修改设定
1. 打开设置窗口 → 角色设定标签页
2. 修改名字、性格等
3. 保存并对话
4. 验证 System Prompt 是否更新

### 测试场景 3: 记忆学习
1. 在对话中告诉角色一些信息（如"我喜欢喝咖啡"）
2. 角色应使用 edit_persona 工具记录
3. 检查 character.json 中的 learned_facts

### 测试场景 4: 敏感字段确认
1. 在对话中提出修改关系（如"以后你当我姐姐吧"）
2. 角色应先确认，得到许可后再修改

---

## 已知限制

1. **记忆搜索**: 目前不支持基于内容的记忆搜索
2. **记忆重要性**: 所有记忆同等权重，无法区分重要程度
3. **批量导入/导出**: 设置窗口尚未实现导入/导出功能
4. **记忆清理**: 需要手动删除旧记忆

---

## 后续改进方向

### Phase 4 可能的增强:
1. 添加记忆重要性评分
2. 实现记忆搜索和过滤
3. 支持批量导入/导出设定
4. 添加预设角色模板
5. 实现记忆自动清理策略（基于时间或重要性）

---

## 总结

Phase 3 成功实现了完整的角色设定与记忆系统，包括：

✅ CharacterPersona 模型 - 完整的角色设定数据结构
✅ CharacterManager - 角色设定管理和持久化
✅ persona_edit Tool - Function Calling 工具集成
✅ 第一次启动引导对话 - 自然对话式引导
✅ 设置窗口角色设定标签页 - 完整的 UI 界面

所有功能已实现并通过基本测试，可以进入 Phase 4 的开发。
