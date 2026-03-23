# Skills Manager
import sys
from pathlib import Path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import json
from datetime import datetime

from .constants import SKILLS_FILE, DEFAULT_SKILLS
from .logger import get_logger

logger = get_logger()


@dataclass
class Skill:
    """技能定义"""
    id: str
    name: str
    description: str
    enabled: bool = True


class SkillsManager:
    """技能管理器"""

    def __init__(self, file_path: Path = SKILLS_FILE):
        self.file_path = file_path
        self.skills: List[Skill] = self._load_or_create()
        self._skill_index: Dict[str, Skill] = {skill.id: skill for skill in self.skills}

    def _load_or_create(self) -> List[Skill]:
        """加载或创建技能配置"""
        if self.file_path.exists():
            try:
                data = json.loads(self.file_path.read_text(encoding="utf-8"))
                skills = [Skill(**skill) for skill in data.get("skills", [])]
                logger.info("技能配置已加载")
                return skills
            except Exception as e:
                logger.error(f"加载技能配置失败: {e}")

        logger.info("创建默认技能配置")
        return [Skill(**skill) for skill in DEFAULT_SKILLS]

    def save(self):
        """保存技能配置"""
        data = {
            "skills": [asdict(skill) for skill in self.skills],
            "updated_at": datetime.utcnow().isoformat()
        }

        self.file_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        logger.info("技能配置已保存")

    def is_enabled(self, skill_id: str) -> bool:
        """检查技能是否启用"""
        skill = self._skill_index.get(skill_id)
        return skill.enabled if skill else False

    def enable(self, skill_id: str):
        """启用技能"""
        if skill_id in self._skill_index:
            self._skill_index[skill_id].enabled = True
            self.save()

    def disable(self, skill_id: str):
        """禁用技能"""
        if skill_id in self._skill_index:
            self._skill_index[skill_id].enabled = False
            self.save()

    def toggle(self, skill_id: str):
        """切换技能状态"""
        if skill_id in self._skill_index:
            skill = self._skill_index[skill_id]
            skill.enabled = not skill.enabled
            self.save()

    def enable_all(self):
        """启用所有技能"""
        for skill in self.skills:
            skill.enabled = True
        self.save()

    def disable_all(self):
        """禁用所有技能"""
        for skill in self.skills:
            skill.enabled = False
        self.save()

    def get_enabled_tools(self) -> List[str]:
        """获取所有启用的工具 ID"""
        # 技能 ID 与工具 ID 的映射
        skill_to_tools = {
            "time": ["get_current_time"],
            "weather": ["get_weather"],
            "todo": ["add_todo", "list_todos", "complete_todo"],
            "clipboard": ["get_clipboard", "set_clipboard"],
            "system": ["get_system_info"],
            "launcher": ["open_application"],
            "scheduler": [],  # 定时任务暂时不在工具列表中
            "persona_edit": ["edit_persona"],
            "motion_control": ["play_motion"]
        }

        enabled_tools = []
        for skill_id, tool_ids in skill_to_tools.items():
            if self.is_enabled(skill_id):
                enabled_tools.extend(tool_ids)

        return enabled_tools

    def reset_to_default(self):
        """重置为默认配置"""
        self.skills = [Skill(**skill) for skill in DEFAULT_SKILLS]
        self._skill_index = {skill.id: skill for skill in self.skills}
        self.save()


# 全局技能管理器实例
_skills_manager: Optional[SkillsManager] = None


def get_skills_manager() -> SkillsManager:
    """获取全局技能管理器"""
    global _skills_manager
    if _skills_manager is None:
        _skills_manager = SkillsManager()
    return _skills_manager
