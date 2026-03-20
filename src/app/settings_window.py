# Settings Window
import sys
from pathlib import Path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTabWidget, QWidget,
    QFormLayout, QLineEdit, QComboBox, QCheckBox,
    QSpinBox, QDoubleSpinBox, QPushButton, QTextEdit,
    QListWidget, QListWidgetItem, QHBoxLayout, QLabel,
    QFileDialog, QGroupBox, QScrollArea
)
from PySide6.QtCore import Qt

from utils import get_config, get_character_manager, get_logger

logger = get_logger()


class SettingsWindow(QDialog):
    """设置窗口"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = get_config()
        self.character_manager = get_character_manager()
        self._setup_ui()
        self._load_values()
        self._setup_window()

    def _setup_window(self):
        """设置窗口"""
        self.setWindowTitle("设置")
        self.setMinimumSize(600, 500)

    def _setup_ui(self):
        """设置 UI"""
        layout = QVBoxLayout(self)

        # 标签页
        self.tabs = QTabWidget()

        # 各个标签页
        self.tabs.addTab(self._create_llm_tab(), "LLM")
        self.tabs.addTab(self._create_live2d_tab(), "Live2D")
        self.tabs.addTab(self._create_character_tab(), "角色设定")
        self.tabs.addTab(self._create_skills_tab(), "技能")
        self.tabs.addTab(self._create_general_tab(), "通用")

        layout.addWidget(self.tabs)

        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        reset_btn = QPushButton("重置")
        reset_btn.clicked.connect(self._reset)
        button_layout.addWidget(reset_btn)

        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self._save)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)

    def _create_llm_tab(self) -> QWidget:
        """创建 LLM 标签页"""
        widget = QWidget()
        layout = QFormLayout(widget)

        # 提供商
        self.llm_provider = QComboBox()
        self.llm_provider.addItems(["openai", "anthropic", "ollama"])
        layout.addRow("提供商:", self.llm_provider)

        # 模型
        self.llm_model = QLineEdit()
        self.llm_model.setPlaceholderText("gpt-4 / claude-3-opus / llama2")
        layout.addRow("模型:", self.llm_model)

        # API Key
        self.llm_api_key = QLineEdit()
        self.llm_api_key.setEchoMode(QLineEdit.Password)
        layout.addRow("API Key:", self.llm_api_key)

        # Base URL
        self.llm_base_url = QLineEdit()
        self.llm_base_url.setPlaceholderText("https://api.openai.com/v1 (可选)")
        layout.addRow("Base URL:", self.llm_base_url)

        # 测试按钮
        test_btn = QPushButton("测试连接")
        layout.addRow("", test_btn)

        return widget

    def _create_live2d_tab(self) -> QWidget:
        """创建 Live2D 标签页"""
        widget = QWidget()
        layout = QFormLayout(widget)

        # 模型路径
        path_layout = QHBoxLayout()
        self.live2d_model_path = QLineEdit()
        path_layout.addWidget(self.live2d_model_path)
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self._browse_live2d_model)
        path_layout.addWidget(browse_btn)
        layout.addRow("模型路径:", path_layout)

        # 缩放
        self.live2d_scale = QDoubleSpinBox()
        self.live2d_scale.setRange(0.5, 2.0)
        self.live2d_scale.setSingleStep(0.1)
        layout.addRow("缩放:", self.live2d_scale)

        layout.addRow(QLabel("动作设置:"))

        # 启用心情驱动动作
        self.motion_enable_mood = QCheckBox("启用心情驱动动作")
        layout.addRow(self.motion_enable_mood)

        # 启用空闲动作
        self.motion_enable_idle = QCheckBox("启用空闲动作")
        layout.addRow(self.motion_enable_idle)

        # 空闲间隔
        self.motion_idle_interval = QSpinBox()
        self.motion_idle_interval.setRange(10, 300)
        self.motion_idle_interval.setSuffix(" 秒")
        layout.addRow("空闲间隔:", self.motion_idle_interval)

        return widget

    def _create_character_tab(self) -> QWidget:
        """创建角色设定标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QFormLayout(scroll_content)

        # 基础信息
        scroll_layout.addRow(QLabel("<b>基础信息</b>"))

        self.char_name = QLineEdit()
        scroll_layout.addRow("名字:", self.char_name)

        self.char_gender = QComboBox()
        self.char_gender.addItems(["", "女", "男", "其他"])
        scroll_layout.addRow("性别:", self.char_gender)

        self.char_age = QLineEdit()
        scroll_layout.addRow("年龄:", self.char_age)

        self.char_birthday = QLineEdit()
        self.char_birthday.setPlaceholderText("YYYY-MM-DD")
        scroll_layout.addRow("生日:", self.char_birthday)

        # 性格设定
        scroll_layout.addRow(QLabel("<b>性格设定</b>"))

        self.char_personality = QLineEdit()
        scroll_layout.addRow("性格:", self.char_personality)

        self.char_speech_style = QLineEdit()
        scroll_layout.addRow("口癖/说话风格:", self.char_speech_style)

        self.char_first_person = QLineEdit()
        scroll_layout.addRow("自称:", self.char_first_person)

        self.char_second_person = QLineEdit()
        scroll_layout.addRow("对用户的称呼:", self.char_second_person)

        # 关系
        scroll_layout.addRow(QLabel("<b>关系设定</b>"))

        self.char_relationship = QLineEdit()
        scroll_layout.addRow("与用户的关系:", self.char_relationship)

        self.char_user_nickname = QLineEdit()
        scroll_layout.addRow("用户昵称:", self.char_user_nickname)

        # 背景
        scroll_layout.addRow(QLabel("<b>背景故事</b>"))

        self.char_background = QTextEdit()
        self.char_background.setMaximumHeight(100)
        scroll_layout.addRow(self.char_background)

        # 喜好
        scroll_layout.addRow(QLabel("<b>喜好设定</b>"))

        self.char_likes = QLineEdit()
        self.char_likes.setPlaceholderText("用逗号分隔")
        scroll_layout.addRow("喜欢:", self.char_likes)

        self.char_dislikes = QLineEdit()
        self.char_dislikes.setPlaceholderText("用逗号分隔")
        scroll_layout.addRow("讨厌:", self.char_dislikes)

        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        return widget

    def _create_skills_tab(self) -> QWidget:
        """创建技能标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.skills_list = QListWidget()
        layout.addWidget(self.skills_list)

        # 按钮
        btn_layout = QHBoxLayout()
        select_all_btn = QPushButton("全选")
        select_all_btn.clicked.connect(self._select_all_skills)
        btn_layout.addWidget(select_all_btn)

        deselect_all_btn = QPushButton("反选")
        deselect_all_btn.clicked.connect(self._deselect_all_skills)
        btn_layout.addWidget(deselect_all_btn)

        layout.addLayout(btn_layout)

        return widget

    def _create_general_tab(self) -> QWidget:
        """创建通用标签页"""
        widget = QWidget()
        layout = QFormLayout(widget)

        # 开机自启
        self.general_auto_start = QCheckBox("开机自启动")
        layout.addRow(self.general_auto_start)

        # 窗口置顶
        self.general_always_on_top = QCheckBox("窗口置顶")
        layout.addRow(self.general_always_on_top)

        # 音效
        self.general_sound_enabled = QCheckBox("启用音效")
        layout.addRow(self.general_sound_enabled)

        return widget

    def _load_values(self):
        """加载值"""
        # LLM
        self.llm_provider.setCurrentText(self.config.llm.provider)
        self.llm_model.setText(self.config.llm.model or "")
        self.llm_api_key.setText(self.config.llm.api_key or "")
        self.llm_base_url.setText(self.config.llm.base_url or "")

        # Live2D
        self.live2d_model_path.setText(self.config.live2d.model_path)
        self.live2d_scale.setValue(self.config.live2d.scale)
        self.motion_enable_mood.setChecked(self.config.motion.enable_mood_motion)
        self.motion_enable_idle.setChecked(self.config.motion.enable_idle_motion)
        self.motion_idle_interval.setValue(self.config.motion.idle_interval_seconds)

        # Character
        persona = self.character_manager.persona
        self.char_name.setText(persona.name)
        self.char_gender.setCurrentText(persona.gender)
        self.char_age.setText(persona.age)
        self.char_birthday.setText(persona.birthday)
        self.char_personality.setText(persona.personality)
        self.char_speech_style.setText(persona.speech_style)
        self.char_first_person.setText(persona.first_person)
        self.char_second_person.setText(persona.second_person)
        self.char_relationship.setText(persona.relationship)
        self.char_user_nickname.setText(persona.user_nickname)
        self.char_background.setPlainText(persona.background)
        self.char_likes.setText(", ".join(persona.likes))
        self.char_dislikes.setText(", ".join(persona.dislikes))

        # Skills
        from ..utils.constants import DEFAULT_SKILLS
        self._skills_data = DEFAULT_SKILLS.copy()
        for skill in self._skills_data:
            item = QListWidgetItem(f"{skill['name']} - {skill['description']}")
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if skill['enabled'] else Qt.CheckState.Unchecked)
            self.skills_list.addItem(item)

        # General
        self.general_auto_start.setChecked(self.config.general.auto_start)
        self.general_always_on_top.setChecked(self.config.general.always_on_top)
        self.general_sound_enabled.setChecked(self.config.general.sound_enabled)

    def _save(self):
        """保存设置"""
        # LLM
        self.config.llm.provider = self.llm_provider.currentText()
        self.config.llm.model = self.llm_model.text()
        self.config.llm.api_key = self.llm_api_key.text() or None
        self.config.llm.base_url = self.llm_base_url.text() or None

        # Live2D
        self.config.live2d.model_path = self.live2d_model_path.text()
        self.config.live2d.scale = self.live2d_scale.value()
        self.config.motion.enable_mood_motion = self.motion_enable_mood.isChecked()
        self.config.motion.enable_idle_motion = self.motion_enable_idle.isChecked()
        self.config.motion.idle_interval_seconds = self.motion_idle_interval.value()

        # Character
        persona = self.character_manager.persona
        persona.name = self.char_name.text()
        persona.gender = self.char_gender.currentText()
        persona.age = self.char_age.text()
        persona.birthday = self.char_birthday.text()
        persona.personality = self.char_personality.text()
        persona.speech_style = self.char_speech_style.text()
        persona.first_person = self.char_first_person.text()
        persona.second_person = self.char_second_person.text()
        persona.relationship = self.char_relationship.text()
        persona.user_nickname = self.char_user_nickname.text()
        persona.background = self.char_background.toPlainText()
        persona.likes = [s.strip() for s in self.char_likes.text().split(",") if s.strip()]
        persona.dislikes = [s.strip() for s in self.char_dislikes.text().split(",") if s.strip()]

        # Skills
        for i, skill in enumerate(self._skills_data):
            item = self.skills_list.item(i)
            skill['enabled'] = item.checkState() == Qt.CheckState.Checked

        # General
        self.config.general.auto_start = self.general_auto_start.isChecked()
        self.config.general.always_on_top = self.general_always_on_top.isChecked()
        self.config.general.sound_enabled = self.general_sound_enabled.isChecked()

        # 保存
        self.config.save()
        self.character_manager.save()

        logger.info("设置已保存")
        self.accept()

    def _reset(self):
        """重置"""
        self._load_values()

    def _browse_live2d_model(self):
        """浏览 Live2D 模型"""
        path = QFileDialog.getExistingDirectory(self, "选择 Live2D 模型目录")
        if path:
            self.live2d_model_path.setText(path)

    def _select_all_skills(self):
        """全选技能"""
        for i in range(self.skills_list.count()):
            item = self.skills_list.item(i)
            item.setCheckState(Qt.CheckState.Checked)

    def _deselect_all_skills(self):
        """反选技能"""
        for i in range(self.skills_list.count()):
            item = self.skills_list.item(i)
            current = item.checkState()
            item.setCheckState(
                Qt.CheckState.Unchecked if current == Qt.CheckState.Checked else Qt.CheckState.Checked
            )
