# Tools Settings Page
import sys
from pathlib import Path
src_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_path))

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QPushButton
)
from PySide6.QtCore import Qt

from .styles import ANIME_STYLE
from utils import get_logger

logger = get_logger()


class ToolsSettingsPage(QWidget):
    """工具设置页面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._tools_data = []
        self._setup_ui()
        self._load_config()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 标题
        title = QLabel("🔧 工具管理")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        layout.addWidget(title)
        
        hint = QLabel("勾选启用工具，取消勾选禁用")
        hint.setStyleSheet("color: #999; font-size: 11px;")
        layout.addWidget(hint)
        
        # 工具列表
        self.tools_list = QListWidget()
        self.tools_list.setStyleSheet("""
            QListWidget {
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                background-color: white;
            }
            QListWidget::item {
                padding: 12px;
                border-bottom: 1px solid #f0f0f0;
            }
            QListWidget::item:selected {
                background-color: #e8f4ff;
                color: #333;
            }
        """)
        layout.addWidget(self.tools_list)
        
        # 按钮
        btn_layout = QHBoxLayout()
        
        select_all_btn = QPushButton("全选")
        select_all_btn.setObjectName("secondaryBtn")
        select_all_btn.clicked.connect(self._select_all)
        btn_layout.addWidget(select_all_btn)
        
        deselect_all_btn = QPushButton("反选")
        deselect_all_btn.setObjectName("secondaryBtn")
        deselect_all_btn.clicked.connect(self._deselect_all)
        btn_layout.addWidget(deselect_all_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
    
    def _load_config(self):
        """加载配置"""
        from agent.tools.tools_config import get_tools_config
        tools_config = get_tools_config()
        self._tools_data = []
        
        for tool in tools_config.tools:
            tool_data = {
                'id': tool.id,
                'name': tool.name,
                'description': tool.description,
                'enabled': tool.enabled
            }
            self._tools_data.append(tool_data)
            
            item = QListWidgetItem(f"🔧 {tool.name} - {tool.description}")
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if tool.enabled else Qt.CheckState.Unchecked)
            self.tools_list.addItem(item)
    
    def _select_all(self):
        """全选"""
        for i in range(self.tools_list.count()):
            item = self.tools_list.item(i)
            item.setCheckState(Qt.CheckState.Checked)
    
    def _deselect_all(self):
        """反选"""
        for i in range(self.tools_list.count()):
            item = self.tools_list.item(i)
            current = item.checkState()
            item.setCheckState(
                Qt.CheckState.Unchecked if current == Qt.CheckState.Checked else Qt.CheckState.Checked
            )
    
    def save(self):
        """保存配置"""
        from agent.tools.tools_config import get_tools_config
        tools_config = get_tools_config()
        
        for i, tool in enumerate(self._tools_data):
            item = self.tools_list.item(i)
            is_enabled = item.checkState() == Qt.CheckState.Checked
            if is_enabled:
                tools_config.enable(tool['id'])
            else:
                tools_config.disable(tool['id'])
        
        tools_config.save()
        logger.info("工具配置已保存")


# 兼容旧代码的别名
SkillsSettingsPage = ToolsSettingsPage
