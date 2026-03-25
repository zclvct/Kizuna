# Mood Settings Page - 心情表情包设置页面
import sys
from pathlib import Path
src_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_path))

from typing import List

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QGridLayout, QScrollArea, QDialog,
    QFormLayout, QLineEdit, QComboBox, QPushButton,
    QMessageBox, QMenu, QSpinBox, QFileDialog,
    QGroupBox, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QMovie

from .styles import ANIME_STYLE, COMBO_BOX_STYLE, CARD_STYLE, MENU_STYLE
from agent.tools.mood_tool import (
    get_all_moods, add_mood, remove_mood, MoodEntry,
    EMOJI_DIR, MOOD_TYPES, CATEGORY_MOOD, CATEGORY_ACTION
)
from utils import get_logger

logger = get_logger()

# 类型分类选项
CATEGORY_OPTIONS = [
    (CATEGORY_MOOD, "心情类型"),
    (CATEGORY_ACTION, "动作类型"),
]


class MoodCard(QFrame):
    """心情表情包卡片"""
    
    delete_requested = Signal(str)  # mood_id
    
    def __init__(self, mood_entry: MoodEntry):
        super().__init__()
        self.mood_entry = mood_entry
        self._setup_ui()
    
    def _setup_ui(self):
        self.setFixedSize(160, 160)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(CARD_STYLE)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 预览图
        preview_label = QLabel()
        preview_label.setFixedSize(80, 80)
        preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_label.setStyleSheet("background: #f0f0f0; border-radius: 8px;")
        
        # 加载预览
        self._load_preview(preview_label)
        layout.addWidget(preview_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # 分类标签
        category_label = "😊 心情" if self.mood_entry.category == CATEGORY_MOOD else "🎬 动作"
        cat_label = QLabel(category_label)
        cat_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cat_label.setStyleSheet("color: #666; font-size: 10px; background: transparent;")
        layout.addWidget(cat_label)
        
        # 心情/动作类型
        mood_name = MOOD_TYPES.get(self.mood_entry.mood, self.mood_entry.mood)
        mood_label = QLabel(f"{mood_name}")
        mood_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mood_label.setStyleSheet("color: #333; font-size: 12px; font-weight: bold; background: transparent;")
        layout.addWidget(mood_label)
        
        # 时长
        duration_label = QLabel(f"时长: {self.mood_entry.duration // 1000}s")
        duration_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        duration_label.setStyleSheet("color: #999; font-size: 10px; background: transparent;")
        layout.addWidget(duration_label)
    
    def _load_preview(self, label: QLabel):
        """加载预览图"""
        file_path = Path(__file__).parent.parent.parent.parent / self.mood_entry.file_path
        
        if not file_path.exists():
            label.setText("❌")
            return
        
        suffix = file_path.suffix.lower()
        if suffix == '.gif':
            movie = QMovie(str(file_path))
            movie.setScaledSize(label.size())
            label.setMovie(movie)
            movie.start()
            # 保存引用防止被回收
            self._movie = movie
        else:
            pixmap = QPixmap(str(file_path))
            if not pixmap.isNull():
                label.setPixmap(pixmap.scaled(
                    label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                ))
            else:
                label.setText("❌")
    
    def contextMenuEvent(self, event):
        """右键菜单"""
        menu = QMenu(self)
        menu.setStyleSheet(MENU_STYLE)
        
        delete_action = menu.addAction("🗑️ 删除")
        
        action = menu.exec(event.globalPos())
        
        if action == delete_action:
            self.delete_requested.emit(self.mood_entry.id)


class AddMoodDialog(QDialog):
    """添加心情表情包对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._selected_file = None
        self._setup_ui()
    
    def _setup_ui(self):
        self.setWindowTitle("添加表情包")
        self.setMinimumSize(400, 400)
        self.setStyleSheet(ANIME_STYLE)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
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
        
        # 内容容器
        content_widget = QWidget()
        content_widget.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 表单
        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        
        # 类型分类
        self.category_combo = QComboBox()
        for cat_id, cat_name in CATEGORY_OPTIONS:
            self.category_combo.addItem(cat_name, cat_id)
        self.category_combo.setStyleSheet(COMBO_BOX_STYLE)
        self.category_combo.currentIndexChanged.connect(self._on_category_changed)
        form_layout.addRow("类型分类:", self.category_combo)
        
        # 心情/动作类型
        self.mood_combo = QComboBox()
        self._update_mood_options()
        self.mood_combo.setStyleSheet(COMBO_BOX_STYLE)
        form_layout.addRow("表情类型:", self.mood_combo)
        
        # 表情包文件
        file_layout = QHBoxLayout()
        self.file_edit = QLineEdit()
        self.file_edit.setPlaceholderText("选择图片或GIF文件")
        self.file_edit.setReadOnly(True)
        file_layout.addWidget(self.file_edit)
        
        browse_btn = QPushButton("浏览")
        browse_btn.setMaximumWidth(60)
        browse_btn.clicked.connect(self._browse_file)
        file_layout.addWidget(browse_btn)
        form_layout.addRow("表情包文件:", file_layout)
        
        # 预览
        self.preview_label = QLabel("点击浏览选择文件")
        self.preview_label.setFixedSize(120, 120)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("background: #f0f0f0; border-radius: 8px; color: #999;")
        form_layout.addRow("预览:", self.preview_label)
        
        # 显示时长
        duration_layout = QHBoxLayout()
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(1, 30)
        self.duration_spin.setValue(3)
        self.duration_spin.setSuffix(" 秒")
        self.duration_spin.setMaximumWidth(100)
        duration_layout.addWidget(self.duration_spin)
        duration_layout.addStretch()
        form_layout.addRow("显示时长:", duration_layout)
        
        # 描述
        self.desc_edit = QLineEdit()
        self.desc_edit.setPlaceholderText("可选，表情包描述")
        form_layout.addRow("描述:", self.desc_edit)
        
        layout.addLayout(form_layout)
        layout.addStretch()
        
        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("取消")
        cancel_btn.setObjectName("secondaryBtn")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("添加")
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
        
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)
    
    def _on_category_changed(self):
        """类型分类改变时更新选项"""
        self._update_mood_options()
    
    def _update_mood_options(self):
        """更新心情/动作类型选项"""
        self.mood_combo.clear()
        category = self.category_combo.currentData()
        
        if category == CATEGORY_MOOD:
            # 心情类型
            mood_keys = ["happy", "sad", "angry", "excited", "shy", "thinking", "surprised", "love", "confused", "sleepy"]
        else:
            # 动作类型
            mood_keys = ["greeting", "cute", "attack", "hug", "kiss", "cry", "laugh", "doubt", "encourage", "celebrate"]
        
        for key in mood_keys:
            cn_name = MOOD_TYPES.get(key, key)
            self.mood_combo.addItem(f"{cn_name} ({key})", key)
    
    def _browse_file(self):
        """浏览选择文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择表情包",
            str(Path.home()),
            "图片文件 (*.png *.jpg *.jpeg *.gif *.webp *.bmp)"
        )
        
        if file_path:
            self._selected_file = file_path
            self.file_edit.setText(Path(file_path).name)
            self._load_preview(file_path)
    
    def _load_preview(self, file_path: str):
        """加载预览"""
        suffix = Path(file_path).suffix.lower()
        
        if suffix == '.gif':
            movie = QMovie(file_path)
            movie.setScaledSize(self.preview_label.size())
            self.preview_label.setMovie(movie)
            movie.start()
            self._movie = movie
        else:
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                self.preview_label.setPixmap(pixmap.scaled(
                    self.preview_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                ))
            else:
                self.preview_label.setText("无法加载")
    
    def _save(self):
        """保存"""
        if not self._selected_file:
            QMessageBox.warning(self, "提示", "请选择表情包文件")
            return
        
        self.accept()
    
    def get_data(self) -> dict:
        """获取数据"""
        return {
            "mood": self.mood_combo.currentData(),
            "category": self.category_combo.currentData(),
            "file_path": self._selected_file,
            "duration": self.duration_spin.value() * 1000,  # 转换为毫秒
            "description": self.desc_edit.text().strip()
        }


class MoodSettingsPage(QWidget):
    """心情表情包设置页面"""
    
    config_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._moods: List[MoodEntry] = []
        self._setup_ui()
        self._load_moods()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 标题
        title = QLabel("😊 心情表情包配置")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        layout.addWidget(title)
        
        # 提示
        hint = QLabel("点击 ➕ 添加表情包，右键卡片可删除。LLM 会根据心情自动显示对应表情包。")
        hint.setStyleSheet("color: #999; font-size: 11px;")
        hint.setWordWrap(True)
        layout.addWidget(hint)
        
        # 心情分组显示
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        self.cards_layout = QGridLayout(scroll_content)
        self.cards_layout.setSpacing(15)
        self.cards_layout.setContentsMargins(5, 5, 5, 5)
        self.cards_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
    
    def _load_moods(self):
        """加载心情配置"""
        self._moods = get_all_moods()
        self._create_cards()
    
    def _create_cards(self):
        """创建卡片"""
        # 清除现有卡片
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # 添加按钮卡片
        add_card = self._create_add_card()
        self.cards_layout.addWidget(add_card, 0, 0)
        
        # 心情卡片 - 按心情类型分组
        col = 1
        row = 0
        for mood in self._moods:
            card = MoodCard(mood)
            card.delete_requested.connect(self._delete_mood)
            
            self.cards_layout.addWidget(card, row, col)
            col += 1
            if col >= 5:
                col = 0
                row += 1
    
    def _create_add_card(self) -> QFrame:
        """创建添加卡片"""
        card = QFrame()
        card.setFixedSize(160, 160)
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.setStyleSheet(CARD_STYLE)
        
        layout = QVBoxLayout(card)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        add_label = QLabel("➕")
        add_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        add_label.setStyleSheet("font-size: 32px; background: transparent;")
        layout.addWidget(add_label)
        
        hint_label = QLabel("添加表情包")
        hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint_label.setStyleSheet("color: #999; font-size: 11px; background: transparent;")
        layout.addWidget(hint_label)
        
        card.mousePressEvent = lambda e: self._add_mood()
        
        return card
    
    def _add_mood(self):
        """添加心情表情包"""
        dialog = AddMoodDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            try:
                add_mood(
                    mood=data["mood"],
                    source_file=data["file_path"],
                    category=data.get("category", CATEGORY_MOOD),
                    description=data["description"],
                    duration=data["duration"]
                )
                self._load_moods()
                self.config_changed.emit()
            except Exception as e:
                QMessageBox.warning(self, "错误", f"添加失败: {e}")
    
    def _delete_mood(self, mood_id: str):
        """删除心情表情包"""
        reply = QMessageBox.question(
            self, "确认删除",
            "确定要删除这个表情包吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            remove_mood(mood_id)
            self._load_moods()
            self.config_changed.emit()
    
    def save(self):
        """保存（配置已在添加/删除时实时保存）"""
        logger.info("心情配置已保存")
