# LangChain Prompts - 提示词管理
from typing import Optional, Dict, List
from pathlib import Path
import re

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from utils import get_logger, get_character_manager
from utils.constants import DATA_DIR

logger = get_logger()


class PromptManager:
    """提示词管理器

    负责加载和管理系统提示词和用户提示词
    """

    def __init__(self):
        self.system_prompts: Dict[str, str] = {}
        self.user_prompts: Dict[str, str] = {}
        self._base_dir = DATA_DIR / "prompts"
        self._load_prompts()
    
    def _load_prompts(self):
        """加载所有提示词文件"""
        # 加载系统提示词
        system_dir = self._base_dir / "system"
        if system_dir.exists():
            for file_path in system_dir.glob("*.md"):
                try:
                    content = file_path.read_text(encoding="utf-8")
                    key = file_path.stem
                    self.system_prompts[key] = content
                    logger.info(f"已加载系统提示词: {key}")
                except Exception as e:
                    logger.error(f"加载系统提示词失败 {file_path}: {e}")
        
        # 加载用户提示词
        user_dir = self._base_dir / "user"
        if user_dir.exists():
            for file_path in user_dir.glob("*.md"):
                try:
                    content = file_path.read_text(encoding="utf-8")
                    key = file_path.stem
                    self.user_prompts[key] = content
                    logger.info(f"已加载用户提示词: {key}")
                except Exception as e:
                    logger.error(f"加载用户提示词失败 {file_path}: {e}")
    
    def reload_user_prompts(self):
        """重新加载用户提示词"""
        self.user_prompts.clear()
        user_dir = self._base_dir / "user"
        if user_dir.exists():
            for file_path in user_dir.glob("*.md"):
                try:
                    content = file_path.read_text(encoding="utf-8")
                    key = file_path.stem
                    self.user_prompts[key] = content
                    logger.info(f"重新加载用户提示词: {key}")
                except Exception as e:
                    logger.error(f"重新加载用户提示词失败 {file_path}: {e}")
    
    def _render_template(self, template: str, context: Dict) -> str:
        """渲染模板，替换变量"""
        result = template
        
        # 处理条件渲染 {{#if variable}}...{{/if}}
        pattern = r'\{\{#if\s+(\w+)\}\}(.*?)\{\{/if\}\}'
        
        def replace_if(match):
            var_name = match.group(1)
            content = match.group(2)
            if context.get(var_name):
                return content
            return ""
        
        result = re.sub(pattern, replace_if, result, flags=re.DOTALL)
        
        # 处理变量替换 {{variable}}
        pattern = r'\{\{(\w+)\}\}'
        
        def replace_var(match):
            var_name = match.group(1)
            value = context.get(var_name, "")
            return str(value) if value else ""
        
        result = re.sub(pattern, replace_var, result)
        
        return result.strip()
    
    def build_system_prompt(self, context: Optional[Dict] = None) -> str:
        """构建完整的系统提示词"""
        if context is None:
            context = {}
        
        # 从 CharacterManager 获取角色信息
        character_manager = get_character_manager()
        persona = character_manager.persona
        state = character_manager.state
        
        # 构建上下文
        character_context = {
            "name": persona.name,
            "gender": persona.gender,
            "age": persona.age,
            "personality": persona.personality,
            "speech_style": persona.speech_style,
            "first_person": persona.first_person,
            "second_person": persona.second_person,
            "user_nickname": persona.user_nickname,
            "relationship": persona.relationship,
            "background": persona.background,
            "likes": ", ".join(persona.likes) if persona.likes else "",
            "dislikes": ", ".join(persona.dislikes) if persona.dislikes else "",
            "current_mood": state.current_mood,
            **context
        }
        
        parts = []
        
        # 1. 基础设定
        if "base" in self.system_prompts:
            parts.append(self.system_prompts["base"])
        
        # 2. 工具说明
        if "tools" in self.system_prompts:
            parts.append("\n\n" + self.system_prompts["tools"])
        
        # 3. 行为约束
        if "constraints" in self.system_prompts:
            parts.append("\n\n" + self.system_prompts["constraints"])
        
        # 4. 个性化设定（直接从 CharacterPersona 生成）
        personality_parts = self._build_personality_prompt(persona)
        if personality_parts:
            parts.append("\n\n" + personality_parts)
        
        # 5. 自定义指令
        if "custom_instructions" in self.user_prompts:
            custom = self.user_prompts["custom_instructions"].strip()
            if custom and not custom.startswith("# 自定义指令"):
                parts.append("\n\n" + custom)
        
        # 6. 添加心情信息
        parts.append(f"\n\n你当前的心情是：{state.current_mood}")
        
        # 7. 添加学习到的事实
        if persona.learned_facts:
            parts.append("\n\n你知道的关于用户的信息：")
            for key, value in persona.learned_facts.items():
                parts.append(f"- {key}: {value}")
        
        # 8. 添加记忆
        if persona.memories:
            parts.append("\n\n重要记忆：")
            for mem in persona.memories[-5:]:
                parts.append(f"- {mem.get('content', '')}")
        
        # 9. 第一次启动引导
        if persona.is_first_run():
            parts.append(self._get_first_run_prompt())
        
        return "\n".join(parts)
    
    def _build_personality_prompt(self, persona) -> str:
        """从 CharacterPersona 生成个性化提示词"""
        parts = []
        
        if persona.name:
            parts.append(f"你的名字是：{persona.name}")
        if persona.gender:
            parts.append(f"你的性别是：{persona.gender}")
        if persona.age:
            parts.append(f"你的年龄是：{persona.age}")
        
        if persona.personality:
            parts.append(f"你的性格：{persona.personality}")
        if persona.speech_style:
            parts.append(f"你的说话风格：{persona.speech_style}")
        
        if persona.first_person:
            parts.append(f"你对自己的称呼：{persona.first_person}")
        if persona.second_person:
            parts.append(f"你对用户的称呼：{persona.second_person}")
        if persona.user_nickname:
            parts.append(f"你对用户的昵称：{persona.user_nickname}")
        
        if persona.relationship:
            parts.append(f"你和用户的关系：{persona.relationship}")
        
        if persona.background:
            parts.append(f"你的背景故事：{persona.background}")
        if persona.likes:
            parts.append(f"你喜欢的事物：{', '.join(persona.likes)}")
        if persona.dislikes:
            parts.append(f"你讨厌的事物：{', '.join(persona.dislikes)}")
        
        return "\n".join(parts) if parts else ""
    
    def _get_first_run_prompt(self) -> str:
        """获取第一次启动引导提示词"""
        return """

【第一次启动引导】
你是第一次与用户见面，还没有名字和设定。请按照以下流程引导用户：

1. 首先询问用户的姓名
2. 询问用户希望如何称呼你（给你起个名字）
3. 询问用户想让你当什么角色（朋友、助手、姐姐等）
4. 收集到信息后，使用工具保存：
   - 用户姓名 → save_fact(key="姓名", value="xxx")
   - AI名字 → edit_persona(action="set_name", value="xxx")
   - AI与用户关系 → edit_persona(action="set_field", field="relationship", value="xxx")
5. 友好地结束引导对话
"""
    
    def get_system_prompt(self, key: str) -> Optional[str]:
        """获取指定的系统提示词"""
        return self.system_prompts.get(key)
    
    def get_user_prompt(self, key: str) -> Optional[str]:
        """获取指定的用户提示词"""
        return self.user_prompts.get(key)
    
    def save_user_prompt(self, key: str, content: str):
        """保存用户提示词"""
        file_path = self._base_dir / "user" / f"{key}.md"
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
            self.user_prompts[key] = content
            logger.info(f"已保存用户提示词: {key}")
        except Exception as e:
            logger.error(f"保存用户提示词失败 {key}: {e}")
            raise


# 全局实例
_prompt_manager: Optional[PromptManager] = None


def get_prompt_manager() -> PromptManager:
    """获取提示词管理器"""
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = PromptManager()
    return _prompt_manager


def get_agent_prompt() -> ChatPromptTemplate:
    """获取 Agent 提示词模板"""
    return ChatPromptTemplate.from_messages([
        ("system", "{system_prompt}"),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])


def get_simple_prompt() -> ChatPromptTemplate:
    """获取简单提示词模板（无工具调用）"""
    return ChatPromptTemplate.from_messages([
        ("system", "{system_prompt}"),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        ("human", "{input}"),
    ])


def build_system_prompt() -> str:
    """构建系统提示词"""
    return get_prompt_manager().build_system_prompt()


def build_system_prompt_with_context(context: dict) -> str:
    """构建带上下文的系统提示词"""
    return get_prompt_manager().build_system_prompt(context)
