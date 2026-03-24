# General Settings Page
import sys
from pathlib import Path
src_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_path))

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFormLayout, QCheckBox, QFrame
)
from PySide6.QtCore import Qt

from .styles import ANIME_STYLE, COMBO_BOX_STYLE
from utils import get_config, get_logger

logger = get_logger()


class GeneralSettingsPage(QWidget):
    """通用设置页面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = get_config()
        self._setup_ui()
        self._load_config()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 启动设置
        startup_group = self._create_section("🚀 启动设置")
        startup_layout = QVBoxLayout()
        startup_layout.setSpacing(12)
        
        self.auto_start = QCheckBox("开机自启动")
        startup_layout.addWidget(self.auto_start)
        
        self.always_on_top = QCheckBox("窗口置顶")
        startup_layout.addWidget(self.always_on_top)
        
        self.sound_enabled = QCheckBox("启用音效")
        startup_layout.addWidget(self.sound_enabled)
        
        startup_group.setLayout(startup_layout)
        layout.addWidget(startup_group)
        
        # 日志设置
        log_group = self._create_section("📋 日志设置")
        log_layout = QFormLayout()
        log_layout.setSpacing(12)
        
        from PySide6.QtWidgets import QComboBox
        self.log_level = QComboBox()
        self.log_level.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.log_level.setStyleSheet(COMBO_BOX_STYLE)
        log_layout.addRow("日志级别:", self.log_level)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        # 关于信息
        about_group = self._create_section("ℹ️ 关于")
        about_layout = QVBoxLayout()
        about_layout.setSpacing(8)
        
        info_label = QLabel(
            "<b>AI Friend</b> - 二次元桌面助手<br><br>"
            "版本: 1.0.0<br>"
            "作者: AI Assistant<br><br>"
            "一个可爱的桌面宠物，陪伴你的每一天 ✨"
        )
        info_label.setStyleSheet("color: #666; background: transparent;")
        about_layout.addWidget(info_label)
        
        about_group.setLayout(about_layout)
        layout.addWidget(about_group)
        
        layout.addStretch()
    
    def _create_section(self, title: str) -> QFrame:
        """创建分组"""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        
        inner = QVBoxLayout(frame)
        inner.setContentsMargins(15, 15, 15, 15)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #5c9eff; background: transparent;")
        inner.addWidget(title_label)
        
        return frame
    
    def _load_config(self):
        """加载配置"""
        self.auto_start.setChecked(self.config.general.auto_start)
        self.always_on_top.setChecked(self.config.general.always_on_top)
        self.sound_enabled.setChecked(self.config.general.sound_enabled)
        self.log_level.setCurrentText(self.config.general.log_level)
    
    def save(self):
        """保存配置"""
        self.config.general.auto_start = self.auto_start.isChecked()
        self.config.general.always_on_top = self.always_on_top.isChecked()
        self.config.general.sound_enabled = self.sound_enabled.isChecked()
        self.config.general.log_level = self.log_level.currentText()
        
        logger.info("通用配置已保存")
