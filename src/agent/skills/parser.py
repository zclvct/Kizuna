# Skill Parser - SKILL.md 解析器
import os
import tempfile
import zipfile
from pathlib import Path
from typing import Optional

from .models import Skill, SkillMeta

from utils import get_logger

logger = get_logger()

# 文本文件扩展名白名单（与 ClawHub 规范一致）
TEXT_FILE_EXTENSIONS = {
    ".py", ".sh", ".js", ".ts", ".mjs", ".cjs",
    ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf",
    ".md", ".txt", ".csv", ".xml", ".html", ".css", ".scss",
    ".sql", ".r", ".rb", ".go", ".rs", ".java", ".kt",
    ".env", ".gitignore", ".editorconfig",
    ".svg", ".graphql", ".gql",
    ".bash", ".zsh", ".fish",
    ".dockerfile", ".makefile",
    ".ps1", ".bat", ".cmd",
}

# SKILL.md 文件名（大小写不敏感）
SKILL_MD_NAMES = {"SKILL.md", "skill.md", "Skill.md"}


class SkillParser:
    """SKILL.md 解析器"""

    @staticmethod
    def parse_skill_md(content: str) -> tuple:
        """解析 SKILL.md，返回 (SkillMeta, 正文内容)

        Args:
            content: SKILL.md 文件内容

        Returns:
            (SkillMeta, markdown正文)
        """
        meta = SkillMeta(name="unknown", description="")
        body = content

        # 尝试解析 YAML frontmatter
        if content.startswith("---"):
            try:
                import frontmatter
                post = frontmatter.loads(content)
                metadata = post.metadata

                meta.name = metadata.get("name", "unknown")
                meta.description = metadata.get("description", "")
                meta.version = str(metadata.get("version", "1.0.0"))
                meta.emoji = metadata.get("emoji", "")
                meta.homepage = metadata.get("homepage", "")

                # 解析 metadata.openclaw（兼容 clawdbot/clawdis 别名）
                openclaw_meta = metadata.get("metadata", {})
                if isinstance(openclaw_meta, dict):
                    # 支持 metadata.openclaw / metadata.clawdbot / metadata.clawdis
                    for key in ("openclaw", "clawdbot", "clawdis"):
                        if key in openclaw_meta:
                            oc = openclaw_meta[key]
                            if isinstance(oc, dict):
                                requires = oc.get("requires", {})
                                if isinstance(requires, dict):
                                    meta.requires_env = requires.get("env", [])
                                    meta.requires_bins = requires.get("bins", [])
                                    meta.requires_any_bins = requires.get("anyBins", [])
                                meta.primary_env = oc.get("primaryEnv", "")
                                meta.always = oc.get("always", False)
                                meta.skill_key = oc.get("skillKey", "")
                                if "emoji" in oc and not meta.emoji:
                                    meta.emoji = oc["emoji"]
                                if "homepage" in oc and not meta.homepage:
                                    meta.homepage = oc["homepage"]
                                os_list = oc.get("os", [])
                                if isinstance(os_list, list):
                                    meta.os_restrictions = os_list
                            break

                body = post.content

            except ImportError:
                # 如果没有 frontmatter 库，手动简单解析
                logger.warning("python-frontmatter 未安装，使用简易 frontmatter 解析")
                meta, body = SkillParser._simple_parse_frontmatter(content)
            except Exception as e:
                logger.error(f"解析 SKILL.md frontmatter 失败: {e}")
                # 回退：手动解析
                meta, body = SkillParser._simple_parse_frontmatter(content)
        else:
            # 没有 frontmatter，整个内容作为正文
            body = content
            # 尝试从第一行提取 name
            first_line = content.strip().split("\n")[0] if content.strip() else ""
            if first_line.startswith("# "):
                meta.name = first_line[2:].strip()
                meta.description = meta.name

        return meta, body

    @staticmethod
    def _simple_parse_frontmatter(content: str) -> tuple:
        """简易 frontmatter 解析（不依赖第三方库）"""
        meta = SkillMeta(name="unknown", description="")
        body = content

        if not content.startswith("---"):
            return meta, body

        parts = content.split("---", 2)
        if len(parts) < 3:
            return meta, body

        yaml_str = parts[1].strip()
        body = parts[2].strip()

        # 简单解析 YAML 键值对
        for line in yaml_str.split("\n"):
            line = line.strip()
            if ":" not in line:
                continue
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip().strip('"').strip("'")

            if key == "name":
                meta.name = value
            elif key == "description":
                meta.description = value
            elif key == "version":
                meta.version = value
            elif key == "emoji":
                meta.emoji = value
            elif key == "homepage":
                meta.homepage = value

        if not meta.description:
            meta.description = meta.name

        return meta, body

    @staticmethod
    def parse_skill_dir(dir_path: str) -> Optional[Skill]:
        """解析整个 skill 目录

        Args:
            dir_path: skill 目录路径

        Returns:
            Skill 对象，解析失败返回 None
        """
        dir_path = Path(dir_path)
        if not dir_path.is_dir():
            logger.error(f"Skill 目录不存在: {dir_path}")
            return None

        # 查找 SKILL.md
        skill_md_path = None
        for name in SKILL_MD_NAMES:
            candidate = dir_path / name
            if candidate.exists():
                skill_md_path = candidate
                break

        # 也检查一级子目录（ZIP 解压后可能多一层目录）
        if skill_md_path is None:
            for child in dir_path.iterdir():
                if child.is_dir():
                    for name in SKILL_MD_NAMES:
                        candidate = child / name
                        if candidate.exists():
                            skill_md_path = candidate
                            dir_path = child  # 使用包含 SKILL.md 的目录
                            break
                    if skill_md_path:
                        break

        if skill_md_path is None:
            logger.error(f"未找到 SKILL.md: {dir_path}")
            return None

        # 读取 SKILL.md
        try:
            content = skill_md_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.error(f"读取 SKILL.md 失败: {e}")
            return None

        meta, body = SkillParser.parse_skill_md(content)

        # 读取辅助文件
        supporting_files = {}
        for root, _, files in os.walk(dir_path):
            for filename in files:
                filepath = Path(root) / filename
                # 跳过 SKILL.md 本身
                if filepath == skill_md_path:
                    continue
                # 跳过隐藏文件和 .clawhub 目录
                if filename.startswith(".") or ".clawhub" in str(filepath) or ".clawdhub" in str(filepath):
                    continue
                # 检查扩展名白名单
                ext = filepath.suffix.lower()
                if ext in TEXT_FILE_EXTENSIONS or not ext:
                    try:
                        rel_path = str(filepath.relative_to(dir_path))
                        file_content = filepath.read_text(encoding="utf-8", errors="replace")
                        # 限制单个文件大小 500KB
                        if len(file_content) <= 500 * 1024:
                            supporting_files[rel_path] = file_content
                    except Exception:
                        pass

        # 生成 slug
        slug = meta.name or dir_path.name
        slug = slug.lower().replace(" ", "-")

        return Skill(
            slug=slug,
            meta=meta,
            skill_md_content=body,
            supporting_files=supporting_files,
            skill_dir=str(dir_path),
        )

    @staticmethod
    def parse_zip(zip_path: str) -> Optional[Skill]:
        """从 ZIP 压缩包解析 skill（不安装，仅解析预览）

        Args:
            zip_path: ZIP 文件路径

        Returns:
            Skill 对象，解析失败返回 None
        """
        zip_path = Path(zip_path)
        if not zip_path.exists():
            logger.error(f"ZIP 文件不存在: {zip_path}")
            return None

        tmp_dir = tempfile.mkdtemp(prefix="kizuna_skill_")
        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                # 安全检查：防止路径穿越
                for member in zf.namelist():
                    if member.startswith("/") or ".." in member:
                        logger.error(f"ZIP 包含不安全路径: {member}")
                        return None
                zf.extractall(tmp_dir)

            return SkillParser.parse_skill_dir(tmp_dir)
        except zipfile.BadZipFile:
            logger.error(f"无效的 ZIP 文件: {zip_path}")
            return None
        except Exception as e:
            logger.error(f"解析 ZIP 失败: {e}")
            return None
