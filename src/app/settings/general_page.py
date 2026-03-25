# General Settings Page
import sys
from pathlib import Path
src_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_path))

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFormLayout, QCheckBox, QFrame, QSlider, QScrollArea,
    QComboBox, QSizePolicy, QGroupBox
)
from PySide6.QtCore import Qt, Signal

from .styles import ANIME_STYLE, COMBO_BOX_STYLE
from utils import get_config, get_logger

logger = get_logger()


class GeneralSettingsPage(QWidget):
    """通用设置页面"""
    
    # 模型缩放实时更新信号
    scale_changed = Signal(float)
    # 窗口置顶状态变化信号
    always_on_top_changed = Signal(bool)
    # 拖动状态变化信号
    draggable_changed = Signal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = get_config()
        self._setup_ui()
        self._load_config()
    
    def _setup_ui(self):
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #a0a0a0;
            }
        """)
        
        # 滚动内容容器
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background-color: transparent;")
        
        # 内容布局
        layout = QVBoxLayout(scroll_content)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # ====== 启动设置 ======
        startup_group = QGroupBox("🚀 启动设置")
        startup_group.setStyleSheet(self._get_group_style())
        startup_layout = QVBoxLayout(startup_group)
        startup_layout.setSpacing(12)
        
        self.auto_start = QCheckBox("开机自启动")
        startup_layout.addWidget(self.auto_start)
        
        self.always_on_top = QCheckBox("窗口置顶")
        self.always_on_top.stateChanged.connect(self._on_always_on_top_changed)
        startup_layout.addWidget(self.always_on_top)
        
        self.sound_enabled = QCheckBox("启用音效")
        startup_layout.addWidget(self.sound_enabled)
        
        layout.addWidget(startup_group)
        
        # ====== 窗口设置 ======
        window_group = QGroupBox("🪟 窗口设置")
        window_group.setStyleSheet(self._get_group_style())
        window_layout = QVBoxLayout(window_group)
        window_layout.setSpacing(12)
        
        self.draggable = QCheckBox("允许拖动窗口")
        self.draggable.stateChanged.connect(self._on_draggable_changed)
        window_layout.addWidget(self.draggable)
        
        layout.addWidget(window_group)
        
        # ====== 对话设置 ======
        chat_group = QGroupBox("💬 对话设置")
        chat_group.setStyleSheet(self._get_group_style())
        chat_layout = QVBoxLayout(chat_group)
        chat_layout.setSpacing(12)
        
        # 对话模式选择
        mode_layout = QHBoxLayout()
        mode_label = QLabel("对话模式:")
        mode_label.setFixedWidth(80)
        mode_layout.addWidget(mode_label)
        
        self.chat_mode = QComboBox()
        self.chat_mode.addItems(["正常模式", "调试模式"])
        self.chat_mode.setStyleSheet(COMBO_BOX_STYLE)
        self.chat_mode.currentIndexChanged.connect(self._on_chat_mode_changed)
        mode_layout.addWidget(self.chat_mode)
        
        chat_layout.addLayout(mode_layout)
        
        # 调试模式说明
        self.debug_hint = QLabel(
            "💡 调试模式将显示：工具调用、请求参数、\n"
            "   返回结果、思考过程等详细信息"
        )
        self.debug_hint.setStyleSheet("color: #999; font-size: 11px; background: transparent;")
        self.debug_hint.setWordWrap(True)
        chat_layout.addWidget(self.debug_hint)
        
        layout.addWidget(chat_group)
        
        # ====== 模型设置 ======
        model_group = QGroupBox("🎭 模型设置")
        model_group.setStyleSheet(self._get_group_style())
        model_layout = QVBoxLayout(model_group)
        model_layout.setSpacing(12)
        
        # 模型大小滑块
        scale_layout = QHBoxLayout()
        scale_label = QLabel("模型大小:")
        scale_label.setFixedWidth(80)
        scale_layout.addWidget(scale_label)
        
        self.scale_slider = QSlider(Qt.Orientation.Horizontal)
        self.scale_slider.setRange(50, 200)  # 0.5x 到 2.0x
        self.scale_slider.setValue(100)
        self.scale_slider.valueChanged.connect(self._on_scale_changed)
        scale_layout.addWidget(self.scale_slider)
        
        self.scale_value_label = QLabel("100%")
        self.scale_value_label.setFixedWidth(50)
        self.scale_value_label.setStyleSheet("color: #5c9eff; font-weight: bold;")
        scale_layout.addWidget(self.scale_value_label)
        
        model_layout.addLayout(scale_layout)
        
        layout.addWidget(model_group)
        
        # ====== 日志设置 ======
        log_group = QGroupBox("📋 日志设置")
        log_group.setStyleSheet(self._get_group_style())
        log_layout = QFormLayout(log_group)
        log_layout.setSpacing(12)
        
        self.log_level = QComboBox()
        self.log_level.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.log_level.setStyleSheet(COMBO_BOX_STYLE)
        log_layout.addRow("日志级别:", self.log_level)
        
        layout.addWidget(log_group)
        
        # ====== 关于信息 ======
        about_group = QGroupBox("ℹ️ 关于")
        about_group.setStyleSheet(self._get_group_style())
        about_layout = QVBoxLayout(about_group)
        about_layout.setSpacing(8)
        
        info_label = QLabel(
            "<b>AI Friend</b> - 二次元桌面助手<br><br>"
            "版本: 1.0.0<br>"
            "作者: AI Assistant<br><br>"
            "一个可爱的桌面宠物，陪伴你的每一天 ✨"
        )
        info_label.setStyleSheet("color: #666;")
        info_label.setWordWrap(True)
        about_layout.addWidget(info_label)
        
        layout.addWidget(about_group)
        
        # 底部弹性空间
        layout.addStretch()
        
        # 设置滚动区域
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)
    
    def _get_group_style(self) -> str:
        """获取分组样式"""
        return """
            QGroupBox {
                background-color: white;
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
                font-size: 14px;
                color: #5c9eff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 10px;
                background-color: white;
            }
            QCheckBox {
                background: transparent;
            }
            QLabel {
                background: transparent;
            }
            QComboBox {
                background: white;
            }
        """
    
    def _load_config(self):
        """加载配置"""
        self.auto_start.setChecked(self.config.general.auto_start)
        self.always_on_top.setChecked(self.config.general.always_on_top)
        self.sound_enabled.setChecked(self.config.general.sound_enabled)
        self.log_level.setCurrentText(self.config.general.log_level)
        self.draggable.setChecked(self.config.general.draggable)
        
        # 加载模型缩放 (转换为整数百分比)
        scale_percent = int(self.config.general.model_scale * 100)
        self.scale_slider.setValue(scale_percent)
        self.scale_value_label.setText(f"{scale_percent}%")
        
        # 加载对话模式
        chat_mode = self.config.general.chat_mode
        self.chat_mode.setCurrentIndex(0 if chat_mode == "normal" else 1)
    
    def _on_chat_mode_changed(self, index: int):
        """对话模式变化"""
        # 根据模式显示/隐藏提示
        self.debug_hint.setVisible(index == 1)
    
    def _on_scale_changed(self, value: int):
        """模型大小滑块变化"""
        self.scale_value_label.setText(f"{value}%")
        scale = value / 100.0
        self.scale_changed.emit(scale)
    
    def _on_always_on_top_changed(self, state: int):
        """窗口置顶状态变化"""
        self.always_on_top_changed.emit(state == Qt.CheckState.Checked)
    
    def _on_draggable_changed(self, state: int):
        """拖动状态变化"""
        self.draggable_changed.emit(state == Qt.CheckState.Checked)
    
    def save(self):
        """保存配置"""
        self.config.general.auto_start = self.auto_start.isChecked()
        self.config.general.always_on_top = self.always_on_top.isChecked()
        self.config.general.sound_enabled = self.sound_enabled.isChecked()
        self.config.general.log_level = self.log_level.currentText()
        self.config.general.draggable = self.draggable.isChecked()
        self.config.general.model_scale = self.scale_slider.value() / 100.0
        
        # 保存对话模式
        self.config.general.chat_mode = "normal" if self.chat_mode.currentIndex() == 0 else "debug"
        
        logger.info("通用配置已保存")
