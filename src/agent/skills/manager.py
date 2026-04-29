# Skill Manager - 技能生命周期管理
import os
import shutil
import platform
from pathlib import Path
from typing import Optional, List

from .models import Skill, DependencyCheckResult
from .parser import SkillParser
from .config import SkillsConfig, get_skills_config

from utils import get_logger

logger = get_logger()


class SkillManager:
    """技能生命周期管理器"""

    def __init__(self):
        self._skills: dict[str, Skill] = {}
        self._config: SkillsConfig = get_skills_config()
        from utils.constants import DATA_DIR
        self._skills_dir = Path(DATA_DIR) / "skills"
        self._skills_dir.mkdir(parents=True, exist_ok=True)
        self.load_skills()

    def load_skills(self):
        """启动时从磁盘加载所有已安装 skill"""
        self._skills.clear()

        for slug, entry in self._config.get_all_entries().items():
            skill_dir = self._skills_dir / slug
            if not skill_dir.is_dir():
                logger.warning(f"Skill 目录缺失，跳过: {slug}")
                continue

            skill = SkillParser.parse_skill_dir(str(skill_dir))
            if skill:
                skill.enabled = entry.enabled
                skill.installed_at = entry.installed_at
                skill.installed_version = entry.version
                skill.source = entry.source
                self._skills[slug] = skill
                logger.info(f"已加载 skill: {slug} (v{entry.version}, {'启用' if entry.enabled else '禁用'})")

        logger.info(f"共加载 {len(self._skills)} 个 skill")

    def reload(self):
        """重新加载所有 skill"""
        self._config = get_skills_config()
        # 重置全局配置实例以重新读取文件
        from . import config as config_module
        config_module._skills_config = None
        self._config = get_skills_config()
        self.load_skills()

    # --- 导入 ---

    def import_from_zip(self, zip_path: str) -> Optional[Skill]:
        """从 ZIP 压缩包导入 skill

        Args:
            zip_path: ZIP 文件路径

        Returns:
            安装后的 Skill 对象，失败返回 None
        """
        import zipfile

        zip_path = Path(zip_path)
        if not zip_path.exists():
            logger.error(f"ZIP 文件不存在: {zip_path}")
            return None

        # 先解析预览
        skill = SkillParser.parse_zip(str(zip_path))
        if not skill:
            logger.error(f"ZIP 解析失败: {zip_path}")
            return None

        slug = skill.slug

        # 如果已存在，先卸载
        if self._config.has_skill(slug):
            self.uninstall(slug)

        # 解压到 skills 目录
        target_dir = self._skills_dir / slug
        target_dir.mkdir(parents=True, exist_ok=True)

        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                # 安全检查
                for member in zf.namelist():
                    if member.startswith("/") or ".." in member:
                        logger.error(f"ZIP 包含不安全路径: {member}")
                        shutil.rmtree(target_dir, ignore_errors=True)
                        return None

                # 检查是否需要在子目录中提取
                # 如果 ZIP 根目录直接包含 SKILL.md，直接提取
                # 如果 ZIP 根目录只有一个子目录包含 SKILL.md，提取该子目录内容
                names = zf.namelist()
                has_root_skill_md = any(
                    n in names for n in ("SKILL.md", "skill.md", "Skill.md")
                )

                if has_root_skill_md:
                    zf.extractall(str(target_dir))
                else:
                    # 查找包含 SKILL.md 的子目录
                    skill_md_in_subdir = None
                    for name in names:
                        basename = Path(name).name
                        if basename in ("SKILL.md", "skill.md", "Skill.md"):
                            skill_md_in_subdir = str(Path(name).parent)
                            break

                    if skill_md_in_subdir:
                        # 提取子目录内容到目标目录
                        for member in names:
                            if member.startswith(skill_md_in_subdir + "/"):
                                relative = member[len(skill_md_in_subdir) + 1:]
                                if not relative:
                                    continue
                                target_file = target_dir / relative
                                if member.endswith("/"):
                                    target_file.mkdir(parents=True, exist_ok=True)
                                else:
                                    target_file.parent.mkdir(parents=True, exist_ok=True)
                                    with zf.open(member) as src, open(target_file, "wb") as dst:
                                        dst.write(src.read())
                    else:
                        # 没找到 SKILL.md，直接提取全部
                        zf.extractall(str(target_dir))

            # 重新解析安装后的目录
            installed_skill = SkillParser.parse_skill_dir(str(target_dir))
            if not installed_skill:
                shutil.rmtree(target_dir, ignore_errors=True)
                logger.error(f"安装后解析失败: {slug}")
                return None

            installed_skill.enabled = True
            installed_skill.source = "import"
            installed_skill.skill_dir = str(target_dir)
            self._skills[slug] = installed_skill

            # 保存配置
            self._config.add_skill(slug, installed_skill.meta.version, "import")

            logger.info(f"Skill 导入成功: {slug} v{installed_skill.meta.version}")
            return installed_skill

        except Exception as e:
            logger.error(f"ZIP 导入失败: {e}", exc_info=True)
            shutil.rmtree(target_dir, ignore_errors=True)
            return None

    def import_from_dir(self, dir_path: str) -> Optional[Skill]:
        """从本地目录导入 skill

        Args:
            dir_path: 本地目录路径

        Returns:
            安装后的 Skill 对象，失败返回 None
        """
        dir_path = Path(dir_path)
        if not dir_path.is_dir():
            logger.error(f"目录不存在: {dir_path}")
            return None

        # 解析
        skill = SkillParser.parse_skill_dir(str(dir_path))
        if not skill:
            logger.error(f"目录解析失败: {dir_path}")
            return None

        slug = skill.slug

        # 如果已存在，先卸载
        if self._config.has_skill(slug):
            self.uninstall(slug)

        # 复制到 skills 目录
        target_dir = self._skills_dir / slug
        try:
            shutil.copytree(str(dir_path), str(target_dir))
        except Exception as e:
            logger.error(f"复制 skill 目录失败: {e}")
            return None

        # 重新解析
        installed_skill = SkillParser.parse_skill_dir(str(target_dir))
        if not installed_skill:
            shutil.rmtree(target_dir, ignore_errors=True)
            logger.error(f"安装后解析失败: {slug}")
            return None

        installed_skill.enabled = True
        installed_skill.source = "local"
        installed_skill.skill_dir = str(target_dir)
        self._skills[slug] = installed_skill

        # 保存配置
        self._config.add_skill(slug, installed_skill.meta.version, "local")

        logger.info(f"Skill 目录导入成功: {slug} v{installed_skill.meta.version}")
        return installed_skill

    # --- 卸载 ---

    def uninstall(self, slug: str):
        """卸载 skill"""
        if slug in self._skills:
            skill = self._skills[slug]
            # 删除文件
            if skill.skill_dir and Path(skill.skill_dir).exists():
                try:
                    shutil.rmtree(skill.skill_dir)
                except Exception as e:
                    logger.error(f"删除 skill 目录失败: {e}")

            del self._skills[slug]

        self._config.remove_skill(slug)
        logger.info(f"Skill 已卸载: {slug}")

    # --- 启用/禁用 ---

    def enable(self, slug: str):
        """启用 skill"""
        if slug in self._skills:
            self._skills[slug].enabled = True
            self._config.enable_skill(slug)

    def disable(self, slug: str):
        """禁用 skill"""
        if slug in self._skills:
            self._skills[slug].enabled = False
            self._config.disable_skill(slug)

    # --- 查询 ---

    def get_enabled_skills(self) -> List[Skill]:
        """获取所有启用的 skill"""
        return [s for s in self._skills.values() if s.enabled]

    def get_all_skills(self) -> List[Skill]:
        """获取所有已安装的 skill"""
        return list(self._skills.values())

    def get_skill(self, slug: str) -> Optional[Skill]:
        """获取指定 skill"""
        return self._skills.get(slug)

    # --- 依赖检查 ---

    def check_dependencies(self, skill: Skill) -> DependencyCheckResult:
        """检查 skill 的依赖是否满足"""
        result = DependencyCheckResult()

        # 检查 OS 限制
        if skill.meta.os_restrictions:
            current_os = platform.system().lower()
            os_map = {"darwin": "macos", "windows": "win32", "linux": "linux"}
            mapped_os = os_map.get(current_os, current_os)
            if mapped_os not in skill.meta.os_restrictions and current_os not in skill.meta.os_restrictions:
                result.os_mismatch = True
                result.satisfied = False
                result.warnings.append(f"当前系统 {current_os} 不在支持列表中: {skill.meta.os_restrictions}")

        # 检查必需的二进制
        for bin_name in skill.meta.requires_bins:
            if not self._check_bin_exists(bin_name):
                result.missing_bins.append(bin_name)
                result.satisfied = False

        # 检查 anyBins（至少一个存在）
        if skill.meta.requires_any_bins:
            any_found = any(self._check_bin_exists(b) for b in skill.meta.requires_any_bins)
            if not any_found:
                result.missing_bins.extend(skill.meta.requires_any_bins)
                result.satisfied = False
                result.warnings.append(f"需要至少安装以下命令之一: {', '.join(skill.meta.requires_any_bins)}")

        # 检查环境变量（仅警告，不阻止安装）
        for env_name in skill.meta.requires_env:
            if not os.environ.get(env_name):
                result.missing_env.append(env_name)
                result.warnings.append(f"环境变量 {env_name} 未设置（skill 可能需要此变量才能正常工作）")

        return result

    @staticmethod
    def _check_bin_exists(bin_name: str) -> bool:
        """检查二进制是否在 PATH 中"""
        import subprocess
        try:
            if platform.system() == "Windows":
                result = subprocess.run(
                    ["where", bin_name],
                    capture_output=True, timeout=5
                )
            else:
                result = subprocess.run(
                    ["which", bin_name],
                    capture_output=True, timeout=5
                )
            return result.returncode == 0
        except Exception:
            return False


# 全局实例
_skill_manager: Optional[SkillManager] = None


def get_skill_manager() -> SkillManager:
    """获取全局 SkillManager"""
    global _skill_manager
    if _skill_manager is None:
        _skill_manager = SkillManager()
    return _skill_manager


def reset_skill_manager():
    """重置 SkillManager"""
    global _skill_manager
    _skill_manager = None
