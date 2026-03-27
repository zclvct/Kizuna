# Conversation Manager
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
        timestamp: Optional[datetime] = None
    ):
        self.role = role
        self.content = content
        self.timestamp = timestamp or datetime.utcnow()

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Message":
        """从字典创建"""
        ts = data.get("timestamp")
        if ts:
            ts = datetime.fromisoformat(ts)
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=ts
        )


class ConversationManager:
    """对话管理器"""

    def __init__(self, file_path: Path = CONVERSATIONS_FILE):
        self.file_path = file_path
        self.messages: List[Message] = []
        self._max_messages = 100  # 最多保留 100 条消息
        self._load()

    def _load(self):
        """加载对话历史"""
        if not self.file_path.exists():
            return

        try:
            data = json.loads(self.file_path.read_text(encoding="utf-8"))
            self.messages = [Message.from_dict(m) for m in data.get("messages", [])]

            # 启动时即限制最大数量，避免历史过多
            if len(self.messages) > self._max_messages:
                self.messages = self.messages[-self._max_messages:]
                self._save()

            logger.info(f"已加载 {len(self.messages)} 条对话历史")
        except Exception as e:
            logger.error(f"加载对话历史失败: {e}")

    def _save(self):
        """保存对话历史"""
        # 保存前再次限制数量，保证文件中最多 100 条
        if len(self.messages) > self._max_messages:
            self.messages = self.messages[-self._max_messages:]

        data = {
            "messages": [m.to_dict() for m in self.messages]
        }
        self.file_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

    def add_message(self, role: str, content: str) -> Message:
        """添加消息"""
        msg = Message(role=role, content=content)
        self.messages.append(msg)

        # 限制数量
        if len(self.messages) > self._max_messages:
            self.messages = self.messages[-self._max_messages:]

        self._save()
        return msg

    def add_user_message(self, content: str) -> Message:
        """添加用户消息"""
        return self.add_message("user", content)

    def add_assistant_message(self, content: str) -> Message:
        """添加助手消息"""
        return self.add_message("assistant", content)

    def get_recent_messages(self, limit: int = 20) -> List[Dict[str, str]]:
        """获取最近的消息（用于 LLM 上下文）"""
        recent = self.messages[-limit:]
        return [
            {"role": m.role, "content": m.content}
            for m in recent
        ]

    def clear(self):
        """清空对话"""
        self.messages = []
        self._save()
        logger.info("对话历史已清空")


# 全局实例
_conversation_manager: Optional[ConversationManager] = None


def get_conversation_manager() -> ConversationManager:
    """获取对话管理器"""
    global _conversation_manager
    if _conversation_manager is None:
        _conversation_manager = ConversationManager()
    return _conversation_manager
