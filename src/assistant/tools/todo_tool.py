# Todo Tool
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import json

from ...utils import TODO_FILE, get_logger

logger = get_logger()


class TodoItem:
    """待办事项"""

    def __init__(
        self,
        id: str,
        content: str,
        completed: bool = False,
        created_at: Optional[datetime] = None,
        due_date: Optional[str] = None
    ):
        self.id = id
        self.content = content
        self.completed = completed
        self.created_at = created_at or datetime.utcnow()
        self.due_date = due_date

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "content": self.content,
            "completed": self.completed,
            "created_at": self.created_at.isoformat(),
            "due_date": self.due_date
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "TodoItem":
        return cls(
            id=data["id"],
            content=data["content"],
            completed=data.get("completed", False),
            created_at=datetime.fromisoformat(data["created_at"]),
            due_date=data.get("due_date")
        )


class TodoManager:
    """待办事项管理器"""

    def __init__(self, file_path: Path = TODO_FILE):
        self.file_path = file_path
        self.items: List[TodoItem] = []
        self._load()

    def _load(self):
        if not self.file_path.exists():
            return
        try:
            data = json.loads(self.file_path.read_text(encoding="utf-8"))
            self.items = [TodoItem.from_dict(item) for item in data.get("items", [])]
        except Exception as e:
            logger.error(f"加载待办事项失败: {e}")

    def _save(self):
        data = {
            "items": [item.to_dict() for item in self.items]
        }
        self.file_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

    def add(self, content: str, due_date: Optional[str] = None) -> TodoItem:
        import uuid
        item = TodoItem(
            id=str(uuid.uuid4())[:8],
            content=content,
            due_date=due_date
        )
        self.items.append(item)
        self._save()
        return item

    def complete(self, item_id: str) -> bool:
        for item in self.items:
            if item.id == item_id:
                item.completed = True
                self._save()
                return True
        return False

    def delete(self, item_id: str) -> bool:
        for i, item in enumerate(self.items):
            if item.id == item_id:
                self.items.pop(i)
                self._save()
                return True
        return False

    def list_all(self) -> List[TodoItem]:
        return self.items

    def list_pending(self) -> List[TodoItem]:
        return [item for item in self.items if not item.completed]


# 全局管理器
_todo_manager: Optional[TodoManager] = None


def get_todo_manager() -> TodoManager:
    global _todo_manager
    if _todo_manager is None:
        _todo_manager = TodoManager()
    return _todo_manager


async def add_todo(content: str, due_date: Optional[str] = None) -> Dict[str, Any]:
    """添加待办事项"""
    manager = get_todo_manager()
    item = manager.add(content, due_date)
    return {
        "id": item.id,
        "content": item.content,
        "success": True
    }


async def list_todos(only_pending: bool = True) -> Dict[str, Any]:
    """列出待办事项"""
    manager = get_todo_manager()
    items = manager.list_pending() if only_pending else manager.list_all()
    return {
        "todos": [
            {"id": item.id, "content": item.content, "completed": item.completed}
            for item in items
        ],
        "success": True
    }


async def complete_todo(item_id: str) -> Dict[str, Any]:
    """完成待办事项"""
    manager = get_todo_manager()
    success = manager.complete(item_id)
    return {"success": success, "id": item_id}


# 工具定义
TODO_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "add_todo",
            "description": "添加待办事项",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "待办内容"},
                    "due_date": {"type": "string", "description": "截止日期，可选"}
                },
                "required": ["content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_todos",
            "description": "列出待办事项",
            "parameters": {
                "type": "object",
                "properties": {
                    "only_pending": {
                        "type": "boolean",
                        "description": "只显示未完成的，默认 true"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "complete_todo",
            "description": "标记待办事项为完成",
            "parameters": {
                "type": "object",
                "properties": {
                    "item_id": {"type": "string", "description": "待办事项 ID"}
                },
                "required": ["item_id"]
            }
        }
    }
]
