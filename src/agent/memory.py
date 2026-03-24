# LangChain Memory - 基于 LangChain 的记忆管理
from typing import List, Optional, Dict, Any
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
import re

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.chat_history import BaseChatMessageHistory
try:
    from langchain.memory import ConversationBufferMemory
except ImportError:
    from langchain_community.chat_message_histories.in_memory import ChatMessageHistory
    ConversationBufferMemory = None

from utils import get_logger

logger = get_logger()


@dataclass
class Memory:
    """记忆条目"""
    id: str
    content: str
    timestamp: str
    importance: int = 1
    tags: List[str] = field(default_factory=list)
    source: str = "conversation"


@dataclass
class Fact:
    """事实知识"""
    key: str
    value: str
    updated_at: str


class ShortTermMemory:
    """短期记忆（对话历史）"""
    
    def __init__(self, max_messages: int = 50):
        self.messages: List[Dict] = []
        self.max_messages = max_messages
    
    def add(self, role: str, content: str):
        """添加消息"""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        })
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
    
    def get_recent(self, count: int = 20) -> List[Dict]:
        """获取最近的消息"""
        return self.messages[-count:] if count > 0 else self.messages
    
    def clear(self):
        """清空记忆"""
        self.messages.clear()
    
    def to_dict(self) -> Dict:
        return {
            "messages": self.messages,
            "max_messages": self.max_messages
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "ShortTermMemory":
        memory = cls(max_messages=data.get("max_messages", 50))
        memory.messages = data.get("messages", [])
        return memory


class LongTermMemory:
    """长期记忆（MD文件存储）"""
    
    def __init__(self):
        self._base_dir = Path(__file__).parent.parent.parent / "data" / "memories"
        self._long_term_file = self._base_dir / "long_term.md"
        self._facts_file = self._base_dir / "facts.md"
        self.memories: List[Memory] = []
        self.facts: List[Fact] = []
        self._load()
    
    def _load(self):
        """从 MD 文件加载"""
        if self._long_term_file.exists():
            try:
                content = self._long_term_file.read_text(encoding="utf-8")
                self.memories = self._parse_memory_md(content)
                logger.info(f"已加载 {len(self.memories)} 条长期记忆")
            except Exception as e:
                logger.error(f"加载长期记忆失败: {e}")
        
        if self._facts_file.exists():
            try:
                content = self._facts_file.read_text(encoding="utf-8")
                self.facts = self._parse_facts_md(content)
                logger.info(f"已加载 {len(self.facts)} 条事实")
            except Exception as e:
                logger.error(f"加载事实失败: {e}")
    
    def _parse_memory_md(self, content: str) -> List[Memory]:
        """解析 MD 格式的记忆文件"""
        memories = []
        lines = content.split("\n")
        current_memory = None
        current_content = []
        
        for line in lines:
            if line.startswith("### ") and len(line) > 4:
                if current_memory and current_content:
                    current_memory.content = "\n".join(current_content).strip()
                    memories.append(current_memory)
                
                date_str = line[4:].strip()
                current_memory = Memory(
                    id=f"mem_{datetime.utcnow().timestamp()}",
                    content="",
                    timestamp=date_str
                )
                current_content = []
            elif current_memory:
                if line.strip() and not line.startswith("---"):
                    current_content.append(line)
        
        if current_memory and current_content:
            current_memory.content = "\n".join(current_content).strip()
            memories.append(current_memory)
        
        return memories
    
    def _parse_facts_md(self, content: str) -> List[Fact]:
        """解析 MD 格式的事实文件"""
        facts = []
        lines = content.split("\n")
        
        for line in lines:
            if line.strip().startswith("- "):
                match = re.match(r'-\s*([^:]+):\s*(.+)', line.strip()[2:])
                if match:
                    facts.append(Fact(
                        key=match.group(1).strip(),
                        value=match.group(2).strip(),
                        updated_at=datetime.utcnow().isoformat()
                    ))
        
        return facts
    
    def _render_memory_md(self) -> str:
        """渲染记忆为 MD 格式"""
        lines = ["# 长期记忆\n"]
        
        dated_memories: Dict[str, List[Memory]] = {}
        for mem in self.memories:
            date = mem.timestamp[:10] if len(mem.timestamp) >= 10 else mem.timestamp
            if date not in dated_memories:
                dated_memories[date] = []
            dated_memories[date].append(mem)
        
        for date in sorted(dated_memories.keys(), reverse=True):
            lines.append(f"### {date}\n")
            for mem in dated_memories[date]:
                lines.append(f"- {mem.content}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _render_facts_md(self) -> str:
        """渲染事实为 MD 格式"""
        lines = ["# 事实知识库\n\n"]
        lines.append("关于用户的信息：\n")
        
        for fact in self.facts:
            lines.append(f"- {fact.key}: {fact.value}")
        
        return "\n".join(lines)
    
    def save(self):
        """保存到 MD 文件"""
        try:
            self._base_dir.mkdir(parents=True, exist_ok=True)
            
            self._long_term_file.write_text(
                self._render_memory_md(), 
                encoding="utf-8"
            )
            
            self._facts_file.write_text(
                self._render_facts_md(), 
                encoding="utf-8"
            )
            
            logger.info("长期记忆已保存")
        except Exception as e:
            logger.error(f"保存长期记忆失败: {e}")
            raise
    
    def add_memory(self, content: str, importance: int = 1, tags: List[str] = None):
        """添加记忆"""
        memory = Memory(
            id=f"mem_{datetime.utcnow().timestamp()}",
            content=content,
            timestamp=datetime.utcnow().strftime("%Y-%m-%d"),
            importance=importance,
            tags=tags or [],
            source="conversation"
        )
        self.memories.append(memory)
        self.save()
        logger.info(f"已添加记忆: {content[:50]}...")
    
    def set_fact(self, key: str, value: str):
        """设置事实"""
        for fact in self.facts:
            if fact.key == key:
                fact.value = value
                fact.updated_at = datetime.utcnow().isoformat()
                self.save()
                logger.info(f"已更新事实: {key}")
                return
        
        self.facts.append(Fact(
            key=key,
            value=value,
            updated_at=datetime.utcnow().isoformat()
        ))
        self.save()
        logger.info(f"已添加事实: {key}")
    
    def get_fact(self, key: str) -> Optional[str]:
        """获取事实"""
        for fact in self.facts:
            if fact.key == key:
                return fact.value
        return None
    
    def search(self, query: str, limit: int = 5) -> List[Memory]:
        """搜索记忆"""
        results = []
        query_lower = query.lower()
        
        for mem in reversed(self.memories):
            if query_lower in mem.content.lower():
                results.append(mem)
                if len(results) >= limit:
                    break
        
        return results
    
    def get_recent_memories(self, count: int = 10) -> List[Memory]:
        """获取最近的记忆"""
        return self.memories[-count:] if self.memories else []
    
    def get_facts_summary(self) -> str:
        """获取事实摘要"""
        if not self.facts:
            return ""
        return "\n".join([f"- {f.key}: {f.value}" for f in self.facts])


class FileChatMessageHistory(BaseChatMessageHistory):
    """基于文件的消息历史存储"""
    
    def __init__(self, short_term: ShortTermMemory = None):
        self._short_term = short_term or ShortTermMemory()
        self._messages: List[BaseMessage] = []
    
    @property
    def messages(self) -> List[BaseMessage]:
        """获取消息列表"""
        self._sync_from_short_term()
        return self._messages
    
    def _sync_from_short_term(self):
        """从短期记忆同步消息"""
        self._messages = []
        for msg in self._short_term.messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            
            if role == "user":
                self._messages.append(HumanMessage(content=content))
            elif role == "assistant":
                self._messages.append(AIMessage(content=content))
            elif role == "system":
                self._messages.append(SystemMessage(content=content))
    
    def add_message(self, message: BaseMessage) -> None:
        """添加消息"""
        self._messages.append(message)
        
        if isinstance(message, HumanMessage):
            self._short_term.add("user", message.content)
        elif isinstance(message, AIMessage):
            self._short_term.add("assistant", message.content)
    
    def clear(self) -> None:
        """清空消息"""
        self._messages.clear()
        self._short_term.clear()


class AIFriendMemory:
    """AI Friend 记忆管理
    
    封装 LangChain Memory，管理短期和长期记忆
    """
    
    def __init__(self):
        self.short_term = ShortTermMemory()
        self.long_term = LongTermMemory()
        self.chat_history = FileChatMessageHistory(self.short_term)
        # 兼容新旧 LangChain 版本
        if ConversationBufferMemory is not None:
            self.memory = ConversationBufferMemory(
                chat_memory=self.chat_history,
                memory_key="chat_history",
                return_messages=True,
            )
        else:
            self.memory = None
    
    def get_memory(self):
        """获取 LangChain Memory 实例"""
        return self.memory
    
    def add_user_message(self, content: str):
        """添加用户消息"""
        self.chat_history.add_message(HumanMessage(content=content))
    
    def add_ai_message(self, content: str):
        """添加 AI 消息"""
        self.chat_history.add_message(AIMessage(content=content))
    
    def get_messages(self) -> List[BaseMessage]:
        """获取所有消息"""
        return self.chat_history.messages
    
    def clear(self):
        """清空记忆"""
        self.chat_history.clear()
    
    def get_context(self, max_messages: int = 20) -> List[Dict]:
        """获取对话上下文"""
        return self.short_term.get_recent(max_messages)
    
    def search_memories(self, query: str) -> List[Memory]:
        """搜索长期记忆"""
        return self.long_term.search(query)
    
    def add_long_term_memory(self, content: str, importance: int = 1):
        """添加长期记忆"""
        self.long_term.add_memory(content, importance)
    
    def save_fact(self, key: str, value: str):
        """保存事实"""
        self.long_term.set_fact(key, value)
    
    def get_fact(self, key: str) -> Optional[str]:
        """获取事实"""
        return self.long_term.get_fact(key)
    
    def get_facts_summary(self) -> str:
        """获取事实摘要"""
        return self.long_term.get_facts_summary()


# 全局实例
_memory: Optional[AIFriendMemory] = None


def get_langchain_memory() -> AIFriendMemory:
    """获取 LangChain Memory 实例"""
    global _memory
    if _memory is None:
        _memory = AIFriendMemory()
    return _memory
