# Skills Config - 技能配置持久化
import json
from pathlib import Path
from typing import Optional, Dict
from dataclasses import dataclass

from utils import get_logger

logger = get_logger()


@dataclass
class SkillEntry:
    """单个 skill 的配置条目"""
    slug: str
    version: str = "1.0.0"
    enabled: bool = True
    installed_at: str = ""
    source: str = "import"    # import / local


class SkillsConfig:
    """技能配置管理"""

    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            from utils.constants import DATA_DIR
            config_path = str(DATA_DIR / "skills.json")
        self._config_path = Path(config_path)
        self._skills: Dict[str, SkillEntry] = {}
        self._exec_tool_enabled: bool = True
        self._exec_require_confirm: bool = False
        self._exec_timeout: int = 30
        self._load()

    def _load(self):
        """加载配置"""
        if not self._config_path.exists():
            self._save_default()
            return

        try:
            with open(self._config_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            for slug, entry_data in data.get("skills", {}).items():
                if isinstance(entry_data, dict):
                    self._skills[slug] = SkillEntry(
                        slug=slug,
                        version=entry_data.get("version", "1.0.0"),
                        enabled=entry_data.get("enabled", True),
                        installed_at=entry_data.get("installed_at", ""),
                        source=entry_data.get("source", "import"),
                    )

            self._exec_tool_enabled = data.get("exec_tool_enabled", True)
            self._exec_require_confirm = data.get("exec_require_confirm", False)
            self._exec_timeout = data.get("exec_timeout", 30)

        except Exception as e:
            logger.error(f"加载 skills 配置失败: {e}")
            self._save_default()

    def _save_default(self):
        """保存默认配置"""
        self._skills = {}
        self._exec_tool_enabled = True
        self._exec_require_confirm = False
        self._exec_timeout = 30
        self.save()

    def save(self):
        """保存配置到文件"""
        data = {
            "skills": {},
            "exec_tool_enabled": self._exec_tool_enabled,
            "exec_require_confirm": self._exec_require_confirm,
            "exec_timeout": self._exec_timeout,
        }

        for slug, entry in self._skills.items():
            data["skills"][slug] = {
                "slug": entry.slug,
                "version": entry.version,
                "enabled": entry.enabled,
                "installed_at": entry.installed_at,
                "source": entry.source,
            }

        try:
            self._config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存 skills 配置失败: {e}")

    # --- Skill 条目操作 ---

    def add_skill(self, slug: str, version: str = "1.0.0", source: str = "import"):
        """添加 skill 条目"""
        from datetime import datetime
        self._skills[slug] = SkillEntry(
            slug=slug,
            version=version,
            enabled=True,
            installed_at=datetime.now().isoformat(),
            source=source,
        )
        self.save()

    def remove_skill(self, slug: str):
        """移除 skill 条目"""
        if slug in self._skills:
            del self._skills[slug]
            self.save()

    def enable_skill(self, slug: str):
        """启用 skill"""
        if slug in self._skills:
            self._skills[slug].enabled = True
            self.save()

    def disable_skill(self, slug: str):
        """禁用 skill"""
        if slug in self._skills:
            self._skills[slug].enabled = False
            self.save()

    def is_skill_enabled(self, slug: str) -> bool:
        """检查 skill 是否启用"""
        entry = self._skills.get(slug)
        return entry.enabled if entry else False

    def get_skill_entry(self, slug: str) -> Optional[SkillEntry]:
        """获取 skill 条目"""
        return self._skills.get(slug)

    def get_all_entries(self) -> Dict[str, SkillEntry]:
        """获取所有 skill 条目"""
        return dict(self._skills)

    def has_skill(self, slug: str) -> bool:
        """检查 skill 是否已安装"""
        return slug in self._skills

    # --- exec 工具配置 ---

    @property
    def exec_tool_enabled(self) -> bool:
        return self._exec_tool_enabled

    @exec_tool_enabled.setter
    def exec_tool_enabled(self, value: bool):
        self._exec_tool_enabled = value
        self.save()

    @property
    def exec_require_confirm(self) -> bool:
        return self._exec_require_confirm

    @exec_require_confirm.setter
    def exec_require_confirm(self, value: bool):
        self._exec_require_confirm = value
        self.save()

    @property
    def exec_timeout(self) -> int:
        return self._exec_timeout

    @exec_timeout.setter
    def exec_timeout(self, value: int):
        self._exec_timeout = max(5, min(120, value))
        self.save()


# 全局实例
_skills_config: Optional[SkillsConfig] = None


def get_skills_config() -> SkillsConfig:
    """获取全局 Skills 配置"""
    global _skills_config
    if _skills_config is None:
        _skills_config = SkillsConfig()
    return _skills_config
