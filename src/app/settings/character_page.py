# Character Settings Page
import sys
from pathlib import Path
src_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_path))

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFormLayout, QLineEdit, QTextEdit, QFrame,
    QScrollArea
)
from PySide6.QtCore import Qt

from .styles import ANIME_STYLE, COMBO_BOX_STYLE
from utils import get_character_manager, get_logger

logger = get_logger()


class CharacterSettingsPage(QWidget):
    """角色设定页面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.character_manager = get_character_manager()
        self._setup_ui()
        self._load_config()
    
    def _setup_ui(self):
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        # 内容容器
        content_widget = QWidget()
        content_widget.setStyleSheet("background-color: transparent;")
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 基础信息
        basic_group, basic_inner = self._create_section("📝 基础信息")
        basic_layout = QFormLayout()
        basic_layout.setSpacing(12)
        
        self.name = QLineEdit()
        basic_layout.addRow("名字:", self.name)
        
        from PySide6.QtWidgets import QComboBox
        self.gender = QComboBox()
        self.gender.addItems(["", "女", "男", "其他"])
        self.gender.setStyleSheet(COMBO_BOX_STYLE)
        basic_layout.addRow("性别:", self.gender)
        
        self.age = QLineEdit()
        basic_layout.addRow("年龄:", self.age)
        
        self.birthday = QLineEdit()
        self.birthday.setPlaceholderText("YYYY-MM-DD")
        basic_layout.addRow("生日:", self.birthday)
        
        basic_inner.addLayout(basic_layout)
        layout.addWidget(basic_group)
        
        # 性格设定
        personality_group, personality_inner = self._create_section("💫 性格设定")
        personality_layout = QFormLayout()
        personality_layout.setSpacing(12)
        
        self.personality = QLineEdit()
        personality_layout.addRow("性格:", self.personality)
        
        self.speech_style = QLineEdit()
        personality_layout.addRow("口癖/说话风格:", self.speech_style)
        
        self.first_person = QLineEdit()
        personality_layout.addRow("自称:", self.first_person)
        
        self.second_person = QLineEdit()
        personality_layout.addRow("对用户的称呼:", self.second_person)
        
        personality_inner.addLayout(personality_layout)
        layout.addWidget(personality_group)
        
        # 关系设定
        relation_group, relation_inner = self._create_section("💕 关系设定")
        relation_layout = QFormLayout()
        relation_layout.setSpacing(12)
        
        self.relationship = QLineEdit()
        relation_layout.addRow("与用户的关系:", self.relationship)
        
        self.user_nickname = QLineEdit()
        relation_layout.addRow("用户昵称:", self.user_nickname)
        
        relation_inner.addLayout(relation_layout)
        layout.addWidget(relation_group)
        
        # 背景故事
        bg_group, bg_inner = self._create_section("📖 背景故事")
        self.background = QTextEdit()
        self.background.setMaximumHeight(100)
        bg_inner.addWidget(self.background)
        layout.addWidget(bg_group)
        
        # 喜好设定
        likes_group, likes_inner = self._create_section("🎁 喜好设定")
        likes_layout = QFormLayout()
        likes_layout.setSpacing(12)
        
        self.likes = QLineEdit()
        self.likes.setPlaceholderText("用逗号分隔")
        likes_layout.addRow("喜欢:", self.likes)
        
        self.dislikes = QLineEdit()
        self.dislikes.setPlaceholderText("用逗号分隔")
        likes_layout.addRow("讨厌:", self.dislikes)
        
        likes_inner.addLayout(likes_layout)
        layout.addWidget(likes_group)
        
        # 开场白设定
        greeting_group, greeting_inner = self._create_section("👋 开场白")
        self.greeting = QTextEdit()
        self.greeting.setMaximumHeight(80)
        self.greeting.setPlaceholderText("自定义开场白，为空则使用默认问候语。支持使用 {name} 引用用户昵称。")
        greeting_inner.addWidget(self.greeting)
        
        hint = QLabel("💡 提示：可使用 {name} 引用用户昵称，如：\"欢迎回来，{name}！\"")
        hint.setStyleSheet("color: #999; font-size: 10px;")
        greeting_inner.addWidget(hint)
        
        layout.addWidget(greeting_group)
        
        layout.addStretch()
        
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)
    
    def _create_section(self, title: str) -> tuple:
        """创建分组，返回 (frame, content_layout)"""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        
        outer_layout = QVBoxLayout(frame)
        outer_layout.setContentsMargins(15, 15, 15, 15)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #5c9eff; background: transparent;")
        outer_layout.addWidget(title_label)
        
        # 内容布局
        content_layout = QVBoxLayout()
        outer_layout.addLayout(content_layout)
        
        return frame, content_layout
    
    def _load_config(self):
        """加载配置"""
        persona = self.character_manager.persona
        self.name.setText(persona.name)
        self.gender.setCurrentText(persona.gender)
        self.age.setText(persona.age)
        self.birthday.setText(persona.birthday)
        self.personality.setText(persona.personality)
        self.speech_style.setText(persona.speech_style)
        self.first_person.setText(persona.first_person)
        self.second_person.setText(persona.second_person)
        self.relationship.setText(persona.relationship)
        self.user_nickname.setText(persona.user_nickname)
        self.background.setPlainText(persona.background)
        self.likes.setText(", ".join(persona.likes))
        self.dislikes.setText(", ".join(persona.dislikes))
        self.greeting.setPlainText(persona.greeting)
    
    def save(self):
        """保存配置"""
        persona = self.character_manager.persona
        persona.name = self.name.text()
        persona.gender = self.gender.currentText()
        persona.age = self.age.text()
        persona.birthday = self.birthday.text()
        persona.personality = self.personality.text()
        persona.speech_style = self.speech_style.text()
        persona.first_person = self.first_person.text()
        persona.second_person = self.second_person.text()
        persona.relationship = self.relationship.text()
        persona.user_nickname = self.user_nickname.text()
        persona.background = self.background.toPlainText()
        persona.likes = [s.strip() for s in self.likes.text().split(",") if s.strip()]
        persona.dislikes = [s.strip() for s in self.dislikes.text().split(",") if s.strip()]
        persona.greeting = self.greeting.toPlainText()
        
        self.character_manager.save()
        logger.info("角色设定已保存")
