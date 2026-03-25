# LangChain Memory - 基于 LangChain 的记忆管理
from typing import List, Optional, Dict, Any
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
import json
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
    """长期记忆（JSON 文件存储）"""
    
    def __init__(self):
        self._base_dir = Path(__file__).parent.parent.parent / "data" / "memories"
        self._facts_file = self._base_dir / "facts.json"
        self._memories_file = self._base_dir / "memories.json"
        
        # 内存存储
        self.facts: List[Fact] = []
        self.facts_index: Dict[str, Fact] = {}  # 快速查找索引
        self.memories: List[Memory] = []
        
        self._load()
    
    def _load(self):
        """从 JSON 文件加载，自动迁移 MD 数据"""
        self._base_dir.mkdir(parents=True, exist_ok=True)
        
        # 尝试加载 JSON
        facts_loaded = self._load_facts_json()
        memories_loaded = self._load_memories_json()
        
        # 如果 JSON 不存在，尝试从 MD 迁移
        if not facts_loaded:
            facts_loaded = self._migrate_facts_from_md()
        if not memories_loaded:
            memories_loaded = self._migrate_memories_from_md()
        
        logger.info(f"已加载 {len(self.facts)} 条事实, {len(self.memories)} 条记忆")
    
    def _load_facts_json(self) -> bool:
        """加载 JSON 格式的事实"""
        if not self._facts_file.exists():
            return False
        
        try:
            with open(self._facts_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            self.facts = []
            self.facts_index = {}
            for key, item in data.get("facts", {}).items():
                fact = Fact(
                    key=key,
                    value=item.get("value", ""),
                    updated_at=item.get("updated_at", datetime.utcnow().isoformat())
                )
                self.facts.append(fact)
                self.facts_index[key] = fact
            
            return True
        except Exception as e:
            logger.error(f"加载事实 JSON 失败: {e}")
            return False
    
    def _load_memories_json(self) -> bool:
        """加载 JSON 格式的记忆"""
        if not self._memories_file.exists():
            return False
        
        try:
            with open(self._memories_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            self.memories = []
            for item in data.get("memories", []):
                self.memories.append(Memory(
                    id=item.get("id", f"mem_{datetime.utcnow().timestamp()}"),
                    content=item.get("content", ""),
                    timestamp=item.get("timestamp", ""),
                    importance=item.get("importance", 1),
                    tags=item.get("tags", []),
                    source=item.get("source", "conversation")
                ))
            
            return True
        except Exception as e:
            logger.error(f"加载记忆 JSON 失败: {e}")
            return False
    
    def _migrate_facts_from_md(self) -> bool:
        """从 MD 文件迁移事实"""
        md_file = self._base_dir / "facts.md"
        if not md_file.exists():
            return False
        
        try:
            content = md_file.read_text(encoding="utf-8")
            self.facts = self._parse_facts_md(content)
            
            # 构建索引
            self.facts_index = {f.key: f for f in self.facts}
            
            # 保存为 JSON
            self._save_facts()
            logger.info(f"已从 MD 迁移 {len(self.facts)} 条事实到 JSON")
            return True
        except Exception as e:
            logger.error(f"迁移事实失败: {e}")
            return False
    
    def _migrate_memories_from_md(self) -> bool:
        """从 MD 文件迁移记忆"""
        md_file = self._base_dir / "long_term.md"
        if not md_file.exists():
            return False
        
        try:
            content = md_file.read_text(encoding="utf-8")
            self.memories = self._parse_memory_md(content)
            
            # 保存为 JSON
            self._save_memories()
            logger.info(f"已从 MD 迁移 {len(self.memories)} 条记忆到 JSON")
            return True
        except Exception as e:
            logger.error(f"迁移记忆失败: {e}")
            return False
    
    def _parse_facts_md(self, content: str) -> List[Fact]:
        """解析 MD 格式的事实文件（兼容旧数据）"""
        facts = []
        lines = content.split("\n")
        
        for line in lines:
            line = line.strip()
            if line.startswith("- "):
                content_part = line[2:]
                match = re.match(r'([^:]+):\s*(.+)', content_part)
                if match:
                    facts.append(Fact(
                        key=match.group(1).strip(),
                        value=match.group(2).strip(),
                        updated_at=datetime.utcnow().isoformat()
                    ))
        
        return facts
    
    def _parse_memory_md(self, content: str) -> List[Memory]:
        """解析 MD 格式的记忆文件（兼容旧数据）"""
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
    
    def _save_facts(self):
        """保存事实到 JSON"""
        data = {
            "version": 1,
            "facts": {
                f.key: {"value": f.value, "updated_at": f.updated_at}
                for f in self.facts
            }
        }
        
        with open(self._facts_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _save_memories(self):
        """保存记忆到 JSON"""
        data = {
            "version": 1,
            "memories": [
                {
                    "id": m.id,
                    "content": m.content,
                    "timestamp": m.timestamp,
                    "importance": m.importance,
                    "tags": m.tags,
                    "source": m.source
                }
                for m in self.memories
            ]
        }
        
        with open(self._memories_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def save(self):
        """保存到 JSON 文件"""
        try:
            self._save_facts()
            self._save_memories()
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
        """设置事实 - O(1) 查找"""
        now = datetime.utcnow().isoformat()
        
        if key in self.facts_index:
            # 更新现有事实
            fact = self.facts_index[key]
            fact.value = value
            fact.updated_at = now
            logger.info(f"已更新事实: {key}")
        else:
            # 添加新事实
            fact = Fact(key=key, value=value, updated_at=now)
            self.facts.append(fact)
            self.facts_index[key] = fact
            logger.info(f"已添加事实: {key}")
        
        self.save()
    
    def get_fact(self, key: str) -> Optional[str]:
        """获取事实 - O(1) 查找"""
        fact = self.facts_index.get(key)
        return fact.value if fact else None
    
    def search(self, query: str, limit: int = 5) -> List[Memory]:
        """搜索记忆"""
        results = []
        query_lower = query.lower()
        
        # 关键词映射
        keyword_map = {
            "喜欢吃什么": ["食物", "吃", "喜欢", "鸡腿", "美食"],
            "喜欢吃": ["食物", "吃", "喜欢", "鸡腿", "美食"],
            "食物": ["食物", "吃", "鸡腿", "美食"],
            "名字": ["名字", "姓名"],
            "职业": ["职业", "工作"],
            "爱好": ["爱好", "兴趣"],
        }
        
        search_keywords = [query_lower]
        for key, keywords in keyword_map.items():
            if key in query_lower:
                search_keywords.extend(keywords)
        
        for mem in reversed(self.memories):
            content_lower = mem.content.lower()
            for keyword in search_keywords:
                if keyword in content_lower:
                    results.append(mem)
                    break
            if len(results) >= limit:
                break
        
        return results
    
    def search_facts(self, query: str) -> List[Fact]:
        """搜索事实"""
        results = []
        query_lower = query.lower()
        
        # 关键词映射
        keyword_map = {
            "喜欢吃什么": ["食物", "吃", "喜欢"],
            "喜欢吃": ["食物", "吃", "喜欢"],
            "食物": ["食物", "吃"],
            "名字": ["名字", "姓名"],
            "职业": ["职业", "工作"],
        }
        
        search_keywords = [query_lower]
        for key, keywords in keyword_map.items():
            if key in query_lower:
                search_keywords.extend(keywords)
        
        for fact in self.facts:
            key_lower = fact.key.lower()
            value_lower = fact.value.lower()
            for keyword in search_keywords:
                if keyword in key_lower or keyword in value_lower:
                    results.append(fact)
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
