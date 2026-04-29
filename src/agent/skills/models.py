# Skills Data Models - 技能数据模型
from dataclasses import dataclass, field


@dataclass
class SkillMeta:
    """SKILL.md frontmatter 元数据"""
    name: str
    description: str
    version: str = "1.0.0"
    emoji: str = ""
    homepage: str = ""
    primary_env: str = ""
    requires_env: list = field(default_factory=list)
    requires_bins: list = field(default_factory=list)
    requires_any_bins: list = field(default_factory=list)
    os_restrictions: list = field(default_factory=list)
    always: bool = False
    skill_key: str = ""


@dataclass
class Skill:
    """一个完整的 Skill"""
    slug: str
    meta: SkillMeta
    skill_md_content: str          # SKILL.md 正文（指令内容，Agent 看到的部分）
    supporting_files: dict = field(default_factory=dict)  # 辅助文件 {相对路径: 内容}
    enabled: bool = True
    installed_at: str = ""
    installed_version: str = ""
    source: str = "import"         # 来源: import(压缩包导入) / local(本地目录)
    skill_dir: str = ""            # skill 文件夹路径


@dataclass
class DependencyCheckResult:
    """依赖检查结果"""
    satisfied: bool = True
    missing_bins: list = field(default_factory=list)    # 缺少的二进制
    missing_env: list = field(default_factory=list)     # 缺少的环境变量
    os_mismatch: bool = False                           # OS 不匹配
    warnings: list = field(default_factory=list)        # 警告信息

    def to_summary(self) -> str:
        """生成检查结果摘要"""
        parts = []
        if self.missing_bins:
            parts.append(f"缺少命令: {', '.join(self.missing_bins)}")
        if self.missing_env:
            parts.append(f"缺少环境变量: {', '.join(self.missing_env)}")
        if self.os_mismatch:
            parts.append("当前操作系统不支持")
        return "; ".join(parts) if parts else "依赖满足"
