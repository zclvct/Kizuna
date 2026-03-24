# Character Persona Management
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path
import json
import random

from .constants import CHARACTER_FILE, MOODS
from .logger import get_logger

logger = get_logger()


class CharacterPersona(BaseModel):
    """角色设定模型"""
    name: str = Field(default="", description="角色名字")
    gender: str = Field(default="", description="性别")
    age: str = Field(default="", description="年龄")
    birthday: str = Field(default="", description="生日")
    personality: str = Field(default="", description="性格描述")
    speech_style: str = Field(default="", description="说话风格/口癖")
    first_person: str = Field(default="我", description="第一人称称呼")
    second_person: str = Field(default="你", description="对用户的称呼")
    user_nickname: str = Field(default="", description="对用户的昵称")
    relationship: str = Field(default="朋友", description="与用户的关系")
    background: str = Field(default="", description="角色背景故事")
    likes: List[str] = Field(default_factory=list, description="喜欢的事物")
    dislikes: List[str] = Field(default_factory=list, description="讨厌的事物")
    # 开场白配置
    greeting: str = Field(default="", description="开场白（为空则使用默认）")
    # 记忆和事实
    memories: List[Dict] = Field(default_factory=list, description="重要记忆列表")
    learned_facts: Dict[str, str] = Field(default_factory=dict, description="学到的事实")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def is_first_run(self) -> bool:
        """是否是第一次运行（没有名字）"""
        return not self.name


class CharacterState(BaseModel):
    """角色状态（心情等）"""
    current_mood: str = "normal"
    mood_history: List[Dict] = Field(default_factory=list)
    current_motion: Optional[str] = None
    is_motion_playing: bool = False
    last_motion_time: Optional[datetime] = None
    idle_timer_enabled: bool = True
    idle_interval: int = 30

    def update_mood(self, new_mood: str, reason: str = ""):
        """更新心情"""
        if new_mood not in MOODS:
            new_mood = "normal"

        old_mood = self.current_mood
        self.current_mood = new_mood

        self.mood_history.append({
            "old": old_mood,
            "new": new_mood,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat()
        })

        if len(self.mood_history) > 50:
            self.mood_history = self.mood_history[-50:]


class CharacterManager:
    """角色管理器"""

    def __init__(self, file_path: Path = CHARACTER_FILE):
        self.file_path = file_path
        self.persona: CharacterPersona = self._load_or_create()
        self.state: CharacterState = CharacterState()

    def _load_or_create(self) -> CharacterPersona:
        """加载或创建角色设定"""
        if self.file_path.exists():
            try:
                data = json.loads(self.file_path.read_text(encoding="utf-8"))
                persona = CharacterPersona(**data)
                logger.info("角色设定已加载")
                return persona
            except Exception as e:
                logger.error(f"加载角色设定失败: {e}")

        logger.info("创建新的角色设定")
        return CharacterPersona()

    def save(self):
        """保存角色设定"""
        self.persona.updated_at = datetime.utcnow()
        data = self.persona.model_dump()

        # 转换 datetime 为字符串
        data["created_at"] = data["created_at"].isoformat()
        data["updated_at"] = data["updated_at"].isoformat()

        self.file_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        logger.info("角色设定已保存")

    def add_memory(self, content: str):
        """添加记忆"""
        self.persona.memories.append({
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        })
        if len(self.persona.memories) > 100:
            self.persona.memories = self.persona.memories[-100:]
        self.save()

    def set_fact(self, key: str, value: str):
        """设置学到的事实"""
        self.persona.learned_facts[key] = value
        self.save()

    def remove_fact(self, key: str):
        """删除事实"""
        if key in self.persona.learned_facts:
            del self.persona.learned_facts[key]
            self.save()

    def reset_to_default(self):
        """重置为默认设定"""
        self.persona = CharacterPersona()
        self.state = CharacterState()
        self.save()

    def get_random_greeting(self) -> str:
        """获取问候语
        
        优先使用用户设置的开场白，否则使用默认问候语
        """
        # 优先使用自定义开场白
        if self.persona.greeting:
            return self.persona.greeting
        
        # 首次运行时的默认问候语
        if self.persona.is_first_run():
            greetings = [
                "你好，初次见面！我还没有名字，能给我起个名字吗？",
                "嗨！很高兴认识你！请问我该怎么称呼你呢？",
                "你好呀！我是你的新助手，能告诉我你的名字吗？",
            ]
            return random.choice(greetings)
        
        # 非首次运行的问候语
        greetings = [
            f"你好呀！{self.persona.user_nickname or '主人'}，有什么我可以帮你的吗？",
            f"嗨！{self.persona.user_nickname or '你'}回来啦～",
            f"欢迎回来，{self.persona.user_nickname or '朋友'}！今天想聊什么呢？",
        ]
        return random.choice(greetings)


# 全局角色管理器实例
_character_manager: Optional[CharacterManager] = None


def get_character_manager() -> CharacterManager:
    """获取全局角色管理器"""
    global _character_manager
    if _character_manager is None:
        _character_manager = CharacterManager()
    return _character_manager
