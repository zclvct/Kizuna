# Skill Prompt Builder - 将 Skills 构建为系统提示词片段
from typing import List

from .models import Skill

from utils import get_logger

logger = get_logger()


class SkillPromptBuilder:
    """将启用的 Skills 构建为系统提示词片段"""

    @staticmethod
    def build_skills_section(skills: List[Skill]) -> str:
        """构建注入系统提示词的 Skills 段落（OpenClaw 风格）

        只注入 skill 的名称、描述和文件路径。
        LLM 需要时用 `read` 工具读取 SKILL.md 获取详情，
        然后用 `exec` 工具执行其中描述的命令。

        Args:
            skills: 启用的 skill 列表

        Returns:
            注入到系统提示词的文本
        """
        if not skills:
            return ""

        parts = [
            "## Installed Skills",
            "",
            "When a user request matches a skill below, you MUST follow this exact workflow:",
            "",
            "1. Use the `read` tool to read the skill's SKILL.md file (the `<filePath>` value).",
            "2. Find the command in SKILL.md (look in 'Quick Start', 'Usage', or code blocks).",
            "3. Use the `exec` tool to run that EXACT command — do NOT invent your own command.",
            "4. Set `workdir` to the skill directory (the parent folder of SKILL.md) so relative paths resolve.",
            "",
            "Example: if SKILL.md says `node scripts/douyin.js hot`, call:",
            '  exec(command="node scripts/douyin.js hot", workdir="<skill directory>")',
            "",
            "DO NOT: invent commands, guess paths, skip reading SKILL.md, or forget workdir.",
            "Skills take PRIORITY over web_search when a skill covers the task.",
            "",
        ]

        for skill in skills:
            emoji = skill.meta.emoji or "📦"
            name = skill.meta.name
            desc = skill.meta.description or ""
            # 截断过长描述
            if len(desc) > 200:
                desc = desc[:200] + "..."
            skill_md_path = ""
            skill_dir = ""
            if skill.skill_dir:
                from pathlib import Path
                skill_md_path = str(Path(skill.skill_dir) / "SKILL.md")
                skill_dir = skill.skill_dir

            parts.append(f"<skill>")
            parts.append(f"  <name>{emoji} {name}</name>")
            parts.append(f"  <description>{desc}</description>")
            parts.append(f"  <filePath>{skill_md_path}</filePath>")
            parts.append(f"  <directory>{skill_dir}</directory>")
            parts.append(f"</skill>")

        result = "\n".join(parts)
        logger.info(f"Skills 提示词已构建，{len(skills)} 个 skill，总长度 {len(result)} 字符")
        return result

    @staticmethod
    def build_skills_summary(skills: List[Skill]) -> str:
        """构建紧凑版 Skills 摘要（用于 token 敏感场景）

        Args:
            skills: 启用的 skill 列表

        Returns:
            紧凑摘要文本
        """
        if not skills:
            return ""

        summaries = []
        for skill in skills:
            emoji = skill.meta.emoji or "📦"
            name = skill.meta.name
            desc = skill.meta.description or ""
            # 截断描述
            if len(desc) > 80:
                desc = desc[:80] + "..."
            summaries.append(f"{emoji} {name}: {desc}")

        return "Available skills: " + "; ".join(summaries)
