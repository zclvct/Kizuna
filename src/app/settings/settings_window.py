# Settings Window - 设置主窗口
import sys
from pathlib import Path
src_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_path))

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QPushButton, QMessageBox,
    QLabel, QFrame, QLineEdit, QTextEdit, QComboBox, QAbstractSpinBox,
    QSizePolicy, QFormLayout
)
from PySide6.QtCore import Qt, Signal

from .styles import ANIME_STYLE, CARD_STYLE
from .llm_page import LLMSettingsPage
from .live2d_page import Live2DSettingsPage
from .character_page import CharacterSettingsPage
from .skills_page import SkillsSettingsPage
from .general_page import GeneralSettingsPage
from .prompts_page import PromptsSettingsPage
from .mood_page import MoodSettingsPage
from .mcp_page import MCPSettingsPage
from .tasks_page import TasksSettingsPage
from utils import get_config, get_character_manager, get_logger

logger = get_logger()


class SettingsWindow(QDialog):
    """设置窗口"""

    model_changed = Signal(str)  # 模型路径变更信号
    scale_changed = Signal(float)  # 模型缩放变更信号
    always_on_top_changed = Signal(bool)  # 窗口置顶变更信号
    draggable_changed = Signal(bool)  # 拖动状态变更信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = get_config()
        self.character_manager = get_character_manager()
        self._setup_window_flags()
        self._setup_ui()
        self._setup_window()
        self._apply_max_input_width()
    
    def _setup_window_flags(self):
        """设置窗口标志 - 不在任务栏显示"""
        flags = self.windowFlags()
        flags |= Qt.WindowType.Tool
        self.setWindowFlags(flags)

    def _setup_window(self):
        """设置窗口"""
        self.setWindowTitle("⚙️ 设置")
        self.setMinimumSize(760, 620)
        self.setStyleSheet(ANIME_STYLE + "\n" + CARD_STYLE)

    def _setup_ui(self):
        """设置 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # 顶部提示卡片
        header_card = QFrame()
        header_card.setObjectName("card")
        header_layout = QVBoxLayout(header_card)
        header_layout.setContentsMargins(14, 10, 14, 10)
        header_layout.setSpacing(2)

        title_label = QLabel("项目设置")
        title_label.setStyleSheet("font-size: 16px; font-weight: 700; color: #334; background: transparent;")
        subtitle_label = QLabel("建议修改后点击“保存”，会立即同步到主窗口行为。")
        subtitle_label.setStyleSheet("font-size: 12px; color: #6b7893; background: transparent;")
        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)
        layout.addWidget(header_card)

        # 标签页
        self.tabs = QTabWidget()

        # 创建各个页面
        self.llm_page = LLMSettingsPage()
        self.live2d_page = Live2DSettingsPage()
        self.character_page = CharacterSettingsPage()
        self.mood_page = MoodSettingsPage()
        self.skills_page = SkillsSettingsPage()
        self.tasks_page = TasksSettingsPage()
        self.prompts_page = PromptsSettingsPage()
        self.mcp_page = MCPSettingsPage()
        self.general_page = GeneralSettingsPage()
        
        # 连接 Live2D 模型变更信号
        self.live2d_page.model_changed.connect(self._on_model_changed)
        
        # 连接通用设置页面的实时信号
        self.general_page.scale_changed.connect(self.scale_changed.emit)
        self.general_page.always_on_top_changed.connect(self.always_on_top_changed.emit)
        self.general_page.draggable_changed.connect(self.draggable_changed.emit)

        self.tabs.addTab(self.llm_page, "🤖 LLM")
        self.tabs.addTab(self.live2d_page, "🎭 Live2D")
        self.tabs.addTab(self.character_page, "👤 角色")
        self.tabs.addTab(self.mood_page, "😊 心情")
        self.tabs.addTab(self.skills_page, "🔧 工具")
        self.tabs.addTab(self.tasks_page, "⏰ 任务")
        self.tabs.addTab(self.mcp_page, "🔌 MCP")
        self.tabs.addTab(self.prompts_page, "📝 提示词")
        self.tabs.addTab(self.general_page, "⚙️ 通用")

        layout.addWidget(self.tabs)

        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        reset_btn = QPushButton("恢复当前页")
        reset_btn.setObjectName("secondaryBtn")
        reset_btn.clicked.connect(self._reset)
        button_layout.addWidget(reset_btn)

        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self._save)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)
    
    def _apply_max_input_width(self):
        """将所有设置页输入控件宽度设置为可用最大"""
        input_widgets = (
            self.findChildren(QLineEdit)
            + self.findChildren(QTextEdit)
            + self.findChildren(QComboBox)
            + self.findChildren(QAbstractSpinBox)
        )
        for widget in input_widgets:
            widget.setMinimumWidth(0)
            widget.setMaximumWidth(16777215)
            policy = widget.sizePolicy()
            policy.setHorizontalPolicy(QSizePolicy.Policy.Expanding)
            widget.setSizePolicy(policy)

        for form in self.findChildren(QFormLayout):
            form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)

    def _on_model_changed(self, model_path: str):
        """模型变更处理"""
        logger.info(f"模型变更: {model_path}")
        # 更新配置中的模型路径
        self.config.live2d.model_path = model_path
        # 直接转发信号，让主窗口立即刷新模型
        self.model_changed.emit(model_path)

    def _save(self):
        """保存设置"""
        # 保存各个页面
        self.llm_page.save()
        self.live2d_page.save()
        self.character_page.save()
        self.mood_page.save()
        self.skills_page.save()
        self.tasks_page.save()
        self.prompts_page.save()
        self.mcp_page.save()
        self.general_page.save()

        # 保存配置文件
        self.config.save()
        self.character_manager.save()

        from utils import get_tools_config
        tools_config = get_tools_config()
        tools_config.save()

        logger.info("设置已保存")
        QMessageBox.information(self, "保存成功", "设置已保存")
        self.accept()

    def _reset(self):
        """重置"""
        self.llm_page._load_config()
        self.live2d_page._load_config()
        self.character_page._load_config()
        self.mood_page._load_moods()
        self.skills_page._load_config()
        self.tasks_page._refresh_all()
        self.prompts_page.reset()
        self.mcp_page.reset()
        self.general_page._load_config()
