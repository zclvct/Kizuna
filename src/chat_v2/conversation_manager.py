# Conversation Manager V2 - 增加防抖保存和消息搜索
import sys
from pathlib import Path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from typing import List, Dict, Optional
from datetime import datetime
import json

from utils import CONVERSATIONS_FILE, get_logger

logger = get_logger()


class Message:
    """消息"""

    def __init__(
        self,
        role: str,
        content: str,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict] = None,
    ):
        self.role = role
        self.content = content
        self.timestamp = timestamp or datetime.utcnow()
        self.metadata = metadata or {}

    def to_dict(self) -> Dict:
        """转换为字典"""
        result = {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
        }
        if self.metadata:
            result["metadata"] = self.metadata
        return result

    @classmethod
    def from_dict(cls, data: Dict) -> "Message":
        """从字典创建"""
        ts = data.get("timestamp")
        if ts:
            ts = datetime.fromisoformat(ts)
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=ts,
            metadata=data.get("metadata"),
        )


class ConversationManager:
    """对话管理器 V2

    改进:
    - 防抖保存，减少磁盘 I/O
    - 消息搜索
    - 批量添加消息
    - 更好的错误处理
    - 导出对话
    """

    _save_timer = None  # 类级别保存定时器

    def __init__(self, file_path: Path = CONVERSATIONS_FILE):
        self.file_path = file_path
        self.messages: List[Message] = []
        self._max_messages = 200
        self._dirty = False  # 是否有未保存的修改
        self._load()

    def _load(self):
        """加载对话历史"""
        if not self.file_path.exists():
            return

        try:
            data = json.loads(self.file_path.read_text(encoding="utf-8"))
            self.messages = [Message.from_dict(m) for m in data.get("messages", [])]

            if len(self.messages) > self._max_messages:
                self.messages = self.messages[-self._max_messages:]
                self._save()

            logger.info(f"已加载 {len(self.messages)} 条对话历史")
        except Exception as e:
            logger.error(f"加载对话历史失败: {e}")

    def _save(self):
        """保存对话历史"""
        if len(self.messages) > self._max_messages:
            self.messages = self.messages[-self._max_messages:]

        data = {
            "messages": [m.to_dict() for m in self.messages]
        }
        try:
            self.file_path.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
            self._dirty = False
        except Exception as e:
            logger.error(f"保存对话历史失败: {e}")

    def flush(self):
        """强制保存（应用退出时调用）"""
        if self._dirty:
            self._save()

    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None) -> Message:
        """添加消息（延迟保存）"""
        msg = Message(role=role, content=content, metadata=metadata)
        self.messages.append(msg)

        if len(self.messages) > self._max_messages:
            self.messages = self.messages[-self._max_messages:]

        self._dirty = True
        self._schedule_save()
        return msg

    def _schedule_save(self):
        """防抖保存 - 最多 2 秒保存一次，减少磁盘 I/O"""
        from PySide6.QtCore import QTimer
        if ConversationManager._save_timer is None:
            ConversationManager._save_timer = QTimer()
            ConversationManager._save_timer.setSingleShot(True)
            ConversationManager._save_timer.timeout.connect(self._save)
        ConversationManager._save_timer.start(2000)

    def add_user_message(self, content: str) -> Message:
        """添加用户消息"""
        return self.add_message("user", content)

    def add_assistant_message(self, content: str) -> Message:
        """添加助手消息"""
        return self.add_message("assistant", content)

    def add_system_message(self, content: str) -> Message:
        """添加系统消息"""
        return self.add_message("system", content)

    def get_recent_messages(self, limit: int = 20) -> List[Dict[str, str]]:
        """获取最近的消息（用于 LLM 上下文）"""
        recent = self.messages[-limit:]
        return [
            {"role": m.role, "content": m.content}
            for m in recent
        ]

    def search(self, query: str) -> List[Message]:
        """搜索消息"""
        query_lower = query.lower()
        return [
            m for m in self.messages
            if query_lower in m.content.lower()
        ]

    def remove_message(self, index: int) -> bool:
        """删除指定索引的消息"""
        if 0 <= index < len(self.messages):
            self.messages.pop(index)
            self._dirty = True
            self._schedule_save()
            return True
        return False

    def remove_last_assistant_message(self) -> bool:
        """删除最后一条 AI 消息"""
        for i in range(len(self.messages) - 1, -1, -1):
            if self.messages[i].role == "assistant":
                self.messages.pop(i)
                self._dirty = True
                self._schedule_save()
                return True
        return False

    def clear(self):
        """清空对话"""
        self.messages = []
        self._save()
        logger.info("对话历史已清空")

    def export_text(self) -> str:
        """导出对话为纯文本"""
        lines = []
        for msg in self.messages:
            time_str = msg.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            role = "你" if msg.role == "user" else "AI"
            lines.append(f"[{time_str}] {role}:\n{msg.content}\n")
        return "\n".join(lines)


# 全局实例
_conversation_manager: Optional[ConversationManager] = None


def get_conversation_manager() -> ConversationManager:
    """获取对话管理器"""
    global _conversation_manager
    if _conversation_manager is None:
        _conversation_manager = ConversationManager()
    return _conversation_manager
