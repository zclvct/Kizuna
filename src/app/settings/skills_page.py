# Skills Settings Page - 技能管理页面
import sys
from pathlib import Path
src_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_path))

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QScrollArea, QCheckBox, QSpinBox,
    QFileDialog, QMessageBox, QTextEdit, QDialog,
    QGridLayout, QSizePolicy,
)
from PySide6.QtCore import Qt

from .styles import ANIME_STYLE, CARD_STYLE
from utils import get_logger

logger = get_logger()


class SkillPreviewDialog(QDialog):
    """Skill 预览对话框"""

    def __init__(self, skill, dep_result=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"预览 Skill: {skill.meta.name}")
        self.setMinimumSize(600, 450)
        self.setStyleSheet(ANIME_STYLE)
        self._confirmed = False

        layout = QVBoxLayout(self)

        # 标题
        emoji = skill.meta.emoji or "📦"
        title = QLabel(f"{emoji} {skill.meta.name} v{skill.meta.version}")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #333;")
        layout.addWidget(title)

        if skill.meta.description:
            desc = QLabel(skill.meta.description)
            desc.setStyleSheet("color: #666; font-size: 13px;")
            desc.setWordWrap(True)
            layout.addWidget(desc)

        # 依赖检查
        if dep_result:
            dep_frame = QFrame()
            dep_frame.setObjectName("card")
            dep_layout = QVBoxLayout(dep_frame)
            dep_layout.setContentsMargins(10, 8, 10, 8)

            dep_title = QLabel("📋 依赖检查")
            dep_title.setStyleSheet("font-weight: bold; font-size: 13px;")
            dep_layout.addWidget(dep_title)

            if dep_result.satisfied and not dep_result.warnings:
                dep_info = QLabel("✅ 所有依赖满足")
                dep_info.setStyleSheet("color: green;")
            elif dep_result.satisfied:
                dep_info = QLabel("⚠️ 依赖基本满足，但有警告")
                dep_info.setStyleSheet("color: #e6a700;")
            else:
                dep_info = QLabel("❌ 部分依赖缺失")
                dep_info.setStyleSheet("color: red;")
            dep_layout.addWidget(dep_info)

            for w in dep_result.warnings:
                wl = QLabel(f"  • {w}")
                wl.setStyleSheet("color: #888; font-size: 12px;")
                wl.setWordWrap(True)
                dep_layout.addWidget(wl)

            layout.addWidget(dep_frame)

        # SKILL.md 内容
        content_label = QLabel("📄 SKILL.md 内容:")
        content_label.setStyleSheet("font-weight: bold; font-size: 13px; margin-top: 8px;")
        layout.addWidget(content_label)

        content_edit = QTextEdit()
        content_edit.setReadOnly(True)
        content_edit.setPlainText(skill.skill_md_content)
        content_edit.setStyleSheet("""
            QTextEdit {
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                background-color: #fafafa;
                font-family: monospace;
                font-size: 12px;
                padding: 8px;
            }
        """)
        layout.addWidget(content_edit)

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("取消")
        cancel_btn.setObjectName("secondaryBtn")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        confirm_btn = QPushButton("确认导入")
        confirm_btn.clicked.connect(self._on_confirm)
        btn_layout.addWidget(confirm_btn)

        layout.addLayout(btn_layout)

    def _on_confirm(self):
        self._confirmed = True
        self.accept()

    @property
    def confirmed(self):
        return self._confirmed


class SkillsSettingsPage(QWidget):
    """技能管理设置页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._skill_widgets = {}
        self._setup_ui()
        self._load_skills()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical { border: none; background: #f0f0f0; width: 10px; border-radius: 5px; }
            QScrollBar::handle:vertical { background: #c0c0c0; border-radius: 5px; min-height: 20px; }
            QScrollBar::handle:vertical:hover { background: #a0a0a0; }
        """)

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(content)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # 标题
        title = QLabel("🎯 技能管理")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        layout.addWidget(title)

        hint = QLabel("Skills 是 AI 的知识扩展包，教会 AI 如何使用工具完成特定任务")
        hint.setStyleSheet("color: #999; font-size: 11px;")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        # exec 工具设置区
        exec_frame = QFrame()
        exec_frame.setObjectName("card")
        exec_layout = QVBoxLayout(exec_frame)
        exec_layout.setContentsMargins(12, 10, 12, 10)

        exec_title = QLabel("⚙️ 命令执行设置")
        exec_title.setStyleSheet("font-weight: bold; font-size: 13px; color: #333;")
        exec_layout.addWidget(exec_title)

        row1 = QHBoxLayout()
        self.exec_enabled_cb = QCheckBox("启用命令执行工具 (exec)")
        self.exec_enabled_cb.setToolTip("Skills 中的脚本/命令需要此工具来执行")
        row1.addWidget(self.exec_enabled_cb)
        row1.addStretch()
        exec_layout.addLayout(row1)

        row2 = QHBoxLayout()
        self.exec_confirm_cb = QCheckBox("执行前需要用户确认")
        row2.addWidget(self.exec_confirm_cb)

        row2.addWidget(QLabel("  超时:"))
        self.exec_timeout_spin = QSpinBox()
        self.exec_timeout_spin.setRange(5, 120)
        self.exec_timeout_spin.setSuffix(" 秒")
        row2.addWidget(self.exec_timeout_spin)
        row2.addStretch()
        exec_layout.addLayout(row2)

        layout.addWidget(exec_frame)

        # 已安装技能区
        skills_label = QLabel("📦 已安装技能")
        skills_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #333; margin-top: 6px;")
        layout.addWidget(skills_label)

        self.skills_container = QVBoxLayout()
        self.skills_container.setSpacing(8)
        layout.addLayout(self.skills_container)

        self.no_skills_label = QLabel("暂无已安装技能，点击下方按钮导入")
        self.no_skills_label.setStyleSheet("color: #aaa; font-size: 12px; padding: 20px;")
        self.no_skills_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.skills_container.addWidget(self.no_skills_label)

        # 导入按钮
        import_layout = QHBoxLayout()

        import_zip_btn = QPushButton("📂 从 ZIP 导入...")
        import_zip_btn.clicked.connect(self._import_zip)
        import_layout.addWidget(import_zip_btn)

        import_dir_btn = QPushButton("📁 从目录导入...")
        import_dir_btn.setObjectName("secondaryBtn")
        import_dir_btn.clicked.connect(self._import_dir)
        import_layout.addWidget(import_dir_btn)

        import_layout.addStretch()
        layout.addLayout(import_layout)

        layout.addStretch()
        scroll.setWidget(content)
        main_layout.addWidget(scroll)

    def _load_skills(self):
        """加载技能列表和配置"""
        # 加载 exec 配置
        from agent.skills.config import get_skills_config
        config = get_skills_config()
        self.exec_enabled_cb.setChecked(config.exec_tool_enabled)
        self.exec_confirm_cb.setChecked(config.exec_require_confirm)
        self.exec_timeout_spin.setValue(config.exec_timeout)

        # 加载技能列表
        self._refresh_skill_list()

    def _refresh_skill_list(self):
        """刷新技能列表"""
        # 清除旧的 widget
        for slug, widget in self._skill_widgets.items():
            self.skills_container.removeWidget(widget)
            widget.deleteLater()
        self._skill_widgets.clear()

        from agent.skills import get_skill_manager
        manager = get_skill_manager()
        skills = manager.get_all_skills()

        self.no_skills_label.setVisible(len(skills) == 0)

        for skill in skills:
            card = self._create_skill_card(skill)
            self.skills_container.addWidget(card)
            self._skill_widgets[skill.slug] = card

        # 通知 Agent 重建，使系统提示词包含最新的 Skills
        self._notify_agent_reload_skills()

    def _notify_agent_reload_skills(self):
        """通知 Agent 重新加载 Skills（刷新系统提示词）"""
        try:
            from agent.core import get_core
            core = get_core()
            if core:
                core.reload_skills()
        except Exception as e:
            logger.warning(f"通知 Agent 重新加载 Skills 失败: {e}")

    def _create_skill_card(self, skill) -> QFrame:
        """创建单个 skill 卡片"""
        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(12, 10, 12, 10)
        card_layout.setSpacing(4)

        # 第一行: emoji + name + version + enabled
        row1 = QHBoxLayout()
        emoji = skill.meta.emoji or "📦"
        name_label = QLabel(f"{emoji} {skill.meta.name}")
        name_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #333;")
        row1.addWidget(name_label)

        ver_label = QLabel(f"v{skill.meta.version or '1.0.0'}")
        ver_label.setStyleSheet("color: #999; font-size: 11px;")
        row1.addWidget(ver_label)

        row1.addStretch()

        enabled_cb = QCheckBox("启用")
        enabled_cb.setChecked(skill.enabled)
        enabled_cb.setProperty("skill_slug", skill.slug)
        enabled_cb.stateChanged.connect(self._on_skill_toggle)
        row1.addWidget(enabled_cb)
        card_layout.addLayout(row1)

        # 第二行: 描述
        if skill.meta.description:
            desc_label = QLabel(skill.meta.description)
            desc_label.setStyleSheet("color: #666; font-size: 12px;")
            desc_label.setWordWrap(True)
            card_layout.addWidget(desc_label)

        # 第三行: 依赖信息
        from agent.skills import get_skill_manager
        manager = get_skill_manager()
        dep = manager.check_dependencies(skill)
        dep_parts = []
        if skill.meta.requires_bins:
            bins_status = []
            for b in skill.meta.requires_bins:
                bins_status.append(f"{b} {'✅' if b not in dep.missing_bins else '❌'}")
            dep_parts.append("命令: " + ", ".join(bins_status))
        if skill.meta.requires_env:
            env_status = []
            for e in skill.meta.requires_env:
                env_status.append(f"{e} {'✅' if e not in dep.missing_env else '⚠️'}")
            dep_parts.append("环境: " + ", ".join(env_status))

        if dep_parts:
            dep_label = QLabel("  ".join(dep_parts))
            dep_label.setStyleSheet("color: #888; font-size: 11px;")
            dep_label.setWordWrap(True)
            card_layout.addWidget(dep_label)

        # 第四行: 操作按钮
        row_btns = QHBoxLayout()

        preview_btn = QPushButton("预览")
        preview_btn.setObjectName("secondaryBtn")
        preview_btn.setProperty("skill_slug", skill.slug)
        preview_btn.clicked.connect(self._preview_skill)
        row_btns.addWidget(preview_btn)

        uninstall_btn = QPushButton("卸载")
        uninstall_btn.setObjectName("secondaryBtn")
        uninstall_btn.setProperty("skill_slug", skill.slug)
        uninstall_btn.clicked.connect(self._uninstall_skill)
        uninstall_btn.setStyleSheet(
            "QPushButton { background-color: #fff0f0; color: #cc4444; }"
            "QPushButton:hover { background-color: #ffe0e0; }"
        )
        row_btns.addWidget(uninstall_btn)

        row_btns.addStretch()
        card_layout.addLayout(row_btns)

        return card

    def _on_skill_toggle(self, state):
        cb = self.sender()
        slug = cb.property("skill_slug")
        from agent.skills import get_skill_manager
        manager = get_skill_manager()
        if state == Qt.CheckState.Checked.value:
            manager.enable(slug)
        else:
            manager.disable(slug)
        # 通知 Agent 重建系统提示词
        self._notify_agent_reload_skills()

    def _preview_skill(self):
        slug = self.sender().property("skill_slug")
        from agent.skills import get_skill_manager
        manager = get_skill_manager()
        skill = manager.get_skill(slug)
        if not skill:
            return
        dep = manager.check_dependencies(skill)
        dialog = SkillPreviewDialog(skill, dep, self)
        dialog.exec()

    def _uninstall_skill(self):
        slug = self.sender().property("skill_slug")
        from agent.skills import get_skill_manager
        manager = get_skill_manager()
        skill = manager.get_skill(slug)
        if not skill:
            return

        name = skill.meta.name or slug
        reply = QMessageBox.question(
            self, "确认卸载",
            f"确定要卸载技能 \"{name}\" 吗？\n技能文件将被删除。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            manager.uninstall(slug)
            self._refresh_skill_list()
            # _refresh_skill_list 内部已调用 _notify_agent_reload_skills

    def _import_zip(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择 Skill ZIP 文件", "", "ZIP 文件 (*.zip);;所有文件 (*)"
        )
        if not file_path:
            return

        from agent.skills import get_skill_manager, SkillParser
        # 先解析预览
        skill = SkillParser.parse_zip(file_path)
        if not skill:
            QMessageBox.warning(self, "导入失败", "无法解析 ZIP 文件中的 SKILL.md")
            return

        from agent.skills import get_skill_manager as _gm
        manager = _gm()
        dep = manager.check_dependencies(skill)

        dialog = SkillPreviewDialog(skill, dep, self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.confirmed:
            result = manager.import_from_zip(file_path)
            if result:
                QMessageBox.information(self, "导入成功", f"技能 \"{result.meta.name}\" 已安装")
                self._refresh_skill_list()
            else:
                QMessageBox.warning(self, "导入失败", "技能安装过程中出错")

    def _import_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择 Skill 目录")
        if not dir_path:
            return

        from agent.skills import SkillParser, get_skill_manager
        skill = SkillParser.parse_skill_dir(dir_path)
        if not skill:
            QMessageBox.warning(self, "导入失败", "目录中未找到有效的 SKILL.md")
            return

        manager = get_skill_manager()
        dep = manager.check_dependencies(skill)

        dialog = SkillPreviewDialog(skill, dep, self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.confirmed:
            result = manager.import_from_dir(dir_path)
            if result:
                QMessageBox.information(self, "导入成功", f"技能 \"{result.meta.name}\" 已安装")
                self._refresh_skill_list()
            else:
                QMessageBox.warning(self, "导入失败", "技能安装过程中出错")

    def save(self):
        """保存配置"""
        from agent.skills.config import get_skills_config
        config = get_skills_config()
        config.exec_tool_enabled = self.exec_enabled_cb.isChecked()
        config.exec_require_confirm = self.exec_confirm_cb.isChecked()
        config.exec_timeout = self.exec_timeout_spin.value()
        config.save()
        logger.info("Skills 配置已保存")

    def _load_config(self):
        """重新加载配置"""
        from agent.skills import reset_skill_manager
        from agent.skills.config import get_skills_config
        # 重置配置实例
        from agent.skills import config as cfg_module
        cfg_module._skills_config = None
        reset_skill_manager()
        self._load_skills()


# 保留旧名称兼容
ToolsSettingsPage = None  # 不再在此文件中提供 ToolsSettingsPage
