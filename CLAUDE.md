# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**AI Friend** - A full-featured Live2D anime desktop assistant with AI conversation, character persona, dynamic memory, skill toggles, mood-driven animations, and scheduled tasks.

## How to Run

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Run the application
python run.py  # Simplified version (placeholder UI, no import issues)
# OR
python src/main.py  # Full integrated version
```

## Architecture

### Module Structure

```
src/
├── main.py           # Application entry point (full version)
├── app/              # UI layer (main_window.py, tray_icon.py, context_menu.py, settings_window.py, tasks_window.py)
├── live2d/           # Live2D rendering (widget.py, motion_controller.py)
├── chat/             # Chat & LLM (llm_client.py, conversation_manager.py, chat_widget.py, message_bubble.py)
├── assistant/        # Assistant tools (tool_registry.py, function_calling.py, tools/*)
├── scheduler/        # Scheduled tasks (task.py, manager.py, parser.py, storage.py)
└── utils/            # Utilities (config.py, character.py, logger.py, constants.py)
```

### Key Patterns

**Import Strategy**: All modules use absolute imports with path setup at the top of each file:
```python
import sys
from pathlib import Path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))
```

**Global Singletons**: Most modules provide global instances via `get_*()` functions:
- `utils.get_config()` - Configuration
- `utils.get_character_manager()` - Character persona
- `utils.get_logger()` - Logger
- `chat.get_llm_client()` - LLM client
- `chat.get_conversation_manager()` - Conversation history
- `assistant.get_tool_registry()` - Tool registry
- `assistant.get_function_handler()` - Function calling handler
- `scheduler.get_task_manager()` - Task manager
- `scheduler.get_task_storage()` - Task storage

### Data Flow

1. **User Input** → `ChatWidget` → `ConversationManager`
2. **LLM Call** → `LLMClient` (LiteLLM wrapper)
3. **Function Calling** → `FunctionCallingHandler` → `ToolRegistry`
4. **Scheduled Tasks** → `TaskManager` (APScheduler) → triggers `task.action_prompt` via LLM
5. **Live2D Animation** → `MotionController` → mood/intent → `Live2DWidget`

### Configuration & Data

- **Config File**: `data/config.json` (via `utils.config.Config`)
- **Character Data**: `data/character.json` (via `utils.character.CharacterManager`)
- **Conversations**: `data/conversations.json`
- **Scheduled Tasks**: `data/scheduled_tasks.json`
- **Motions Config**: `data/motions.json`
- **Todos**: `data/todos.json`
- **Environment**: `.env` (loaded via python-dotenv)

## Key Modules

### chat/llm_client.py
- Wraps LiteLLM for multi-provider support (OpenAI/Anthropic/Ollama)
- Injects character persona system prompt
- Provides streaming and non-streaming chat methods

### scheduler/manager.py
- Uses APScheduler with CronTrigger only
- Persists tasks to JSON
- Callback interface for task execution

### assistant/tool_registry.py
- Registry pattern for LLM tools
- Converts to OpenAI tool format
- Async tool execution

### Available Tools (assistant/tools/)
- `time_tool` - Get current time/date
- `weather_tool` - Get weather forecasts
- `todo_tool` - Manage todo items
- `clipboard_tool` - Access system clipboard
- `system_tool` - Get system information
- `launcher_tool` - Launch applications/files
- `persona_tool` - Edit character persona
- `motion_tool` - Control Live2D motions

### utils/character.py
- `CharacterPersona` (Pydantic model): name, personality, speech_style, memories, learned_facts
- `CharacterState`: current_mood, conversation_count
- `CharacterManager`: loads/saves, provides `to_system_prompt()`

### Mood & Motion System
- 8 mood types: happy, excited, normal, shy, sad, angry, surprised, thinking
- Motion mapping via `data/motions.json`
- LLM can call `play_motion` tool to trigger animations
- Idle motions play automatically during silence

## Important Notes

1. **Imports**: Always use the absolute import pattern with src_path setup
2. **Entry Points**: `run.py` is the simplified placeholder entry point; `src/main.py` is the full integrated version
3. **Live2D**: Placeholder implementation - WebEngineView fallback option documented in design docs
4. **Docs**: See `docs/` directory for full design documents (in Chinese)
5. **No Test Infrastructure**: No tests configured in the project currently
6. **No Lint/Format Config**: No flake8, black, or other formatting configs present
7. **Async/Await**: LLM and tool operations use async patterns with asyncio
