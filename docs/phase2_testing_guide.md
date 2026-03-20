# Phase 2 测试指南

## 前置准备

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置 LLM
复制 `.env.example` 为 `.env` 并配置：

#### 使用 OpenAI
```env
LLM_PROVIDER=openai
LLM_MODEL=gpt-4
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

#### 使用 Ollama（本地，无需 API Key）
```env
LLM_PROVIDER=ollama
LLM_MODEL=llama2
OLLAMA_BASE_URL=http://localhost:11434
```

#### 使用 Anthropic
```env
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-opus-20240229
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 3. 启动应用
```bash
python src/main.py
```

## 测试项目

### ✅ 测试 1: 基础对话

**测试步骤**:
1. 点击 Live2D 上的 💬 按钮打开对话窗口
2. 在输入框中输入：`你好`
3. 点击发送

**预期结果**:
- 消息气泡显示（打字机效果）
- 角色回复：`你好呀！有什么我可以帮你的吗？`
- Live2D 心情显示为 `😐 平静`

---

### ✅ 测试 2: 流式输出

**测试步骤**:
1. 输入：`请详细介绍一下自己`

**预期结果**:
- 回复逐渐显示（打字机效果）
- 可以看到文字逐字/逐句出现
- 最终显示完整的回复

---

### ✅ 测试 3: 时间工具

**测试步骤**:
1. 输入：`现在几点了？`

**预期结果**:
- 先显示：`🔧 调用: get_current_time`
- 然后流式显示回复，包含当前时间

---

### ✅ 测试 4: 天气工具

**测试步骤**:
1. 输入：`今天北京天气怎么样？`

**预期结果**:
- 先显示：`🔧 调用: get_weather`
- 然后显示天气信息

---

### ✅ 测试 5: 待办事项

**测试步骤**:
1. 输入：`提醒我明天下午3点开会`

**预期结果**:
- 先显示：`🔧 调用: add_todo`
- 然后确认已添加

2. 输入：`查看待办事项`

**预期结果**:
- 先显示：`🔧 调用: list_todos`
- 然后显示待办列表

---

### ✅ 测试 6: 角色学习

**测试步骤**:
1. 输入：`以后你就叫小秘`

**预期结果**:
- 角色回复：`好的，主人！以后我就是小秘了~的说`
- 检查 `data/character.json`，确认名字已保存

2. 输入：`我喜欢喝咖啡`

**预期结果**:
- 角色回复：`记下了！原来主人喜欢喝咖啡呀 ☕`
- 检查 `data/character.json`，确认 `learned_facts` 已更新

---

### ✅ 测试 7: 动作控制

**测试步骤**:
1. 输入：`我很开心`

**预期结果**:
- 先显示：`🔧 调用: play_motion`
- Live2D 动作显示为：`动作: happy_01`
- 心情变为：`😊 开心`

---

### ✅ 测试 8: 多轮对话

**测试步骤**:
1. 输入：`帮我查询天气和当前时间`

**预期结果**:
- 显示：`🔧 调用: get_weather`
- 显示：`🔧 调用: get_current_time`
- 回复整合了天气和时间信息

---

### ✅ 测试 9: 角色设定编辑

**测试步骤**:
1. 输入：`以后你当我姐姐吧`

**预期结果**:
- 角色回复：`哎？要当姐姐吗... 真的可以吗？`
- 等待确认

2. 输入：`嗯，可以`

**预期结果**:
- 角色回复：`好的，老弟/妹妹！姐姐会好好照顾你的 ♡`
- 检查 `data/character.json`，确认关系已更新

---

### ✅ 测试 10: 第一次启动引导

**测试步骤**:
1. 删除 `data/character.json`
2. 重新启动应用
3. 对话窗口自动打开

**预期结果**:
- 角色主动问候：`你好，初次见面！我还没有名字，能给我起个名字吗？`

---

## 常见问题

### Q1: 提示 API Key 错误
**解决**: 检查 `.env` 文件中的 `OPENAI_API_KEY` 是否正确

### Q2: Ollama 连接失败
**解决**:
1. 确保已安装 Ollama: https://ollama.com
2. 启动 Ollama 服务
3. 测试连接: `curl http://localhost:11434/api/generate -d '{"model":"llama2","prompt":"hi"}'`

### Q3: 工具调用失败
**解决**: 检查 LLM 是否支持 Function Calling
- OpenAI: GPT-3.5+, GPT-4
- Anthropic: Claude 3+
- Ollama: 部分模型支持

### Q4: 流式输出不显示
**解决**: 检查 LLM 是否支持流式输出，大多数现代 LLM 都支持

### Q5: 角色设定没有保存
**解决**:
1. 检查 `data/` 目录是否有写权限
2. 查看日志文件，确认没有错误

---

## 数据文件检查

### character.json
位置: `data/character.json`

检查项目:
- ✅ `name` - 角色名字
- ✅ `personality` - 性格描述
- ✅ `speech_style` - 说话风格
- ✅ `learned_facts` - 学到的信息
- ✅ `memories` - 重要记忆

### conversations.json
位置: `data/conversations.json`

检查项目:
- ✅ `messages` - 对话历史
- ✅ 每条消息包含 `role`, `content`, `timestamp`

### motions.json
位置: `data/motions.json`

检查项目:
- ✅ `mood_motions` - 心情动作映射
- ✅ `intent_motions` - 意图动作映射
- ✅ `idle_motions` - 空闲动作列表

---

## 性能测试

### 测试 1: 长文本回复
**测试**: 请求生成一篇长文章
**预期**: 流式输出流畅，无卡顿

### 测试 2: 快速连续发送
**测试**: 快速发送多条消息
**预期**: 每条消息都能正确处理

### 测试 3: 工具调用延迟
**测试**: 调用需要网络请求的工具（天气）
**预期**: 工具执行后正确返回结果

---

## 日志检查

### 查看日志
日志输出到控制台，包含：
- `[INFO]` - 正常信息
- `[ERROR]` - 错误信息
- `[DEBUG]` - 调试信息

### 关键日志
- `Calling LLM: openai/gpt-4` - LLM 调用
- `Executing tool: get_current_time` - 工具执行
- `回复生成完成` - 对话完成
- `角色设定已保存` - 设定保存

---

## 下一步

Phase 2 已完成！可以继续开发：

### Phase 3: 角色设定与记忆
大部分已完成，主要是 UI 部分：
- ✅ CharacterPersona 数据模型
- ✅ CharacterManager
- ✅ persona_edit tool
- ⏳ 设置窗口的"角色设定"标签页（待完善）
- ✅ 第一次启动引导对话

### Phase 4: 技能系统与助手工具
大部分已完成：
- ✅ ToolRegistry
- ✅ 所有工具实现
- ⏳ 设置窗口的"技能"标签页（待完善）
- ✅ 技能开关整合

---

## 总结

Phase 2 实现了完整的对话功能，包括：
- ✅ 流式输出
- ✅ Function Calling
- ✅ 角色设定整合
- ✅ 工具系统
- ✅ 动作控制

所有功能都已测试通过，可以开始下一阶段的开发！
