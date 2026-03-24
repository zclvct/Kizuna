# Prompts Settings Page - 提示词设置页面
import sys
from pathlib import Path
src_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_path))

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTabWidget, QTextEdit, QPushButton, QMessageBox,
    QGroupBox, QScrollArea
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from .styles import ANIME_STYLE
from utils import get_logger

logger = get_logger()


class PromptsSettingsPage(QWidget):
    """提示词设置页面
    
    管理系统提示词（只读）和用户提示词（可编辑）
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._prompt_manager = None
        self._setup_ui()
        self._load_prompts()
    
    @property
    def prompt_manager(self):
        if self._prompt_manager is None:
            from agent import get_prompt_manager
            self._prompt_manager = get_prompt_manager()
        return self._prompt_manager
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 标题
        title = QLabel("📝 提示词管理")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        layout.addWidget(title)
        
        hint = QLabel("系统提示词只读，用户提示词可自定义编辑")
        hint.setStyleSheet("color: #999; font-size: 11px;")
        layout.addWidget(hint)
        
        # 标签页
        self.tabs = QTabWidget()
        
        # 用户提示词标签页
        user_tab = QWidget()
        user_layout = QVBoxLayout(user_tab)
        
        # 自定义指令
        custom_group = QGroupBox("自定义指令 (custom_instructions.md)")
        custom_layout = QVBoxLayout(custom_group)
        self.custom_edit = QTextEdit()
        self.custom_edit.setPlaceholderText("在这里添加自定义指令...\n\n例如：\n- 我更喜欢简洁的回答\n- 请在每天早上提醒我喝水\n- 我喜欢用中文交流")
        self.custom_edit.setFont(QFont("Menlo", 11))
        self.custom_edit.setMinimumHeight(200)
        custom_layout.addWidget(self.custom_edit)
        user_layout.addWidget(custom_group)
        
        # 提示信息
        hint_label = QLabel("💡 提示：角色个性化设定请在「角色设定」页面中配置")
        hint_label.setStyleSheet("color: #666; font-size: 11px; padding: 5px;")
        user_layout.addWidget(hint_label)
        
        user_layout.addStretch()
        self.tabs.addTab(user_tab, "✏️ 用户提示词")
        
        # 系统提示词标签页
        system_tab = QWidget()
        system_layout = QVBoxLayout(system_tab)
        
        # 基础设定
        base_group = QGroupBox("基础设定 (base.md) - 只读")
        base_layout = QVBoxLayout(base_group)
        self.base_view = QTextEdit()
        self.base_view.setReadOnly(True)
        self.base_view.setFont(QFont("Menlo", 11))
        self.base_view.setMinimumHeight(120)
        base_layout.addWidget(self.base_view)
        system_layout.addWidget(base_group)
        
        # 工具说明
        tools_group = QGroupBox("工具说明 (tools.md) - 只读")
        tools_layout = QVBoxLayout(tools_group)
        self.tools_view = QTextEdit()
        self.tools_view.setReadOnly(True)
        self.tools_view.setFont(QFont("Menlo", 11))
        self.tools_view.setMinimumHeight(120)
        tools_layout.addWidget(self.tools_view)
        system_layout.addWidget(tools_group)
        
        # 行为约束
        constraints_group = QGroupBox("行为约束 (constraints.md) - 只读")
        constraints_layout = QVBoxLayout(constraints_group)
        self.constraints_view = QTextEdit()
        self.constraints_view.setReadOnly(True)
        self.constraints_view.setFont(QFont("Menlo", 11))
        self.constraints_view.setMinimumHeight(80)
        constraints_layout.addWidget(self.constraints_view)
        system_layout.addWidget(constraints_group)
        
        system_layout.addStretch()
        self.tabs.addTab(system_tab, "🔒 系统提示词")
        
        layout.addWidget(self.tabs)
    
    def _load_prompts(self):
        """加载提示词"""
        # 用户提示词
        self.custom_edit.setPlainText(
            self.prompt_manager.get_user_prompt("custom_instructions") or ""
        )
        
        # 系统提示词
        self.base_view.setPlainText(
            self.prompt_manager.get_system_prompt("base") or ""
        )
        self.tools_view.setPlainText(
            self.prompt_manager.get_system_prompt("tools") or ""
        )
        self.constraints_view.setPlainText(
            self.prompt_manager.get_system_prompt("constraints") or ""
        )
    
    def save(self):
        """保存用户提示词"""
        try:
            # 保存自定义指令
            custom = self.custom_edit.toPlainText()
            self.prompt_manager.save_user_prompt("custom_instructions", custom)

            # 重新加载提示词
            self.prompt_manager.reload_user_prompts()

            logger.info("用户提示词已保存")

        except Exception as e:
            logger.error(f"保存提示词失败: {e}")
    
    def reset(self):
        """重置为默认值"""
        self._load_prompts()
