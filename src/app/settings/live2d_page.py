# Live2D Settings Page - 模型配置页面
import sys
import json
import shutil
from pathlib import Path
from functools import partial

src_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_path))

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QGridLayout, QScrollArea, QMessageBox,
    QMenu, QFileDialog, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter, QColor, QPen, QBrush

from .styles import CARD_STYLE, MENU_STYLE
from utils import get_config, get_logger
from utils.constants import resolve_path, get_relative_path

logger = get_logger()

# 获取 assets/live2d 目录
ASSETS_LIVE2D_DIR = Path(__file__).parent.parent.parent.parent / "assets" / "live2d"


def validate_live2d_model(model_path: str) -> tuple[bool, str, list[str]]:
    """验证 Live2D 模型是否有效
    
    Args:
        model_path: 模型目录路径
        
    Returns:
        (是否有效, 模型名称, 可用动作列表)
    """
    path = resolve_path(model_path)
    
    if not path.exists():
        return False, "", []
    
    # 查找 .model3.json 文件
    model3_files = list(path.glob("*.model3.json"))
    if not model3_files:
        return False, "", []
    
    model_json_path = model3_files[0]
    model_name = model_json_path.stem.replace(".model3", "")
    
    try:
        with open(model_json_path, 'r', encoding='utf-8') as f:
            model_config = json.load(f)
        
        # 检查必要字段
        file_refs = model_config.get("FileReferences", {})
        moc_file = file_refs.get("Moc", "")
        
        if not moc_file:
            return False, model_name, []
        
        # 检查 moc3 文件是否存在
        moc_path = path / moc_file
        if not moc_path.exists():
            return False, model_name, []
        
        # 提取可用动作
        motions = file_refs.get("Motions", {})
        motion_names = []
        for group_name, motion_list in motions.items():
            for motion_entry in motion_list:
                file_path = motion_entry.get("File", "")
                if file_path:
                    motion_name = Path(file_path).stem
                    if motion_name.endswith(".motion3"):
                        motion_name = motion_name[:-8]
                    motion_names.append(motion_name)
        
        return True, model_name, motion_names
        
    except Exception as e:
        logger.error(f"验证模型失败: {e}")
        return False, model_name, []


class Live2DModelCard(QFrame):
    """Live2D 模型卡片"""
    
    clicked = Signal()
    delete_requested = Signal()
    refresh_requested = Signal()
    
    def __init__(self, model_data: dict, is_default: bool = False, is_add_card: bool = False):
        super().__init__()
        self.model_data = model_data
        self.is_default = is_default
        self.is_add_card = is_add_card
        self._setup_ui()
    
    def _setup_ui(self):
        self.setFixedSize(180, 100)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)
        
        if self.is_add_card:
            self.setObjectName("addCard")
            self.setStyleSheet(CARD_STYLE)
            
            add_label = QLabel("➕")
            add_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            add_label.setStyleSheet("font-size: 28px; background: transparent;")
            layout.addWidget(add_label)
            
            hint_label = QLabel("导入模型")
            hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            hint_label.setStyleSheet("color: #999; font-size: 12px; background: transparent;")
            layout.addWidget(hint_label)
        else:
            self.setObjectName("cardDefault" if self.is_default else "card")
            self.setStyleSheet(CARD_STYLE)
            
            # 模型名称
            name = self.model_data.get('name', 'Unknown')
            name_label = QLabel(name[:12] + ('...' if len(name) > 12 else ''))
            name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            name_label.setStyleSheet("color: #333; font-size: 13px; font-weight: bold; background: transparent;")
            layout.addWidget(name_label)
            
            # 动作数量
            motions = self.model_data.get('motions', [])
            motion_label = QLabel(f"动作: {len(motions)} 个")
            motion_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            motion_label.setStyleSheet("color: #666; font-size: 11px; background: transparent;")
            layout.addWidget(motion_label)
            
            # 状态
            if self.is_default:
                status_label = QLabel("当前默认")
                status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                status_label.setStyleSheet("color: #5c9eff; font-size: 10px; background: transparent;")
                layout.addWidget(status_label)
    
    def set_default(self, is_default: bool):
        """设置是否为默认"""
        self.is_default = is_default
        # 更新样式
        self.setObjectName("cardDefault" if is_default else "card")
        self.setStyleSheet(CARD_STYLE)
        self.update()
    
    def paintEvent(self, event):
        super().paintEvent(event)
        if self.is_default and not self.is_add_card:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # 绘制选中边框
            painter.setPen(QPen(QColor("#5c9eff"), 3))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(1, 1, self.width() - 3, self.height() - 3, 8, 8)
            
            # 绘制勾选标记
            painter.setBrush(QBrush(QColor("#5c9eff")))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(self.width() - 26, 8, 18, 18)
            
            painter.setPen(QPen(QColor("white"), 2))
            painter.drawLine(self.width() - 21, 17, self.width() - 18, 20)
            painter.drawLine(self.width() - 18, 20, self.width() - 13, 13)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
    
    def contextMenuEvent(self, event):
        """右键菜单"""
        if not self.is_add_card:
            menu = QMenu(self)
            menu.setStyleSheet(MENU_STYLE)
            
            set_default_action = menu.addAction("✓ 设为默认")
            refresh_action = menu.addAction("🔄 刷新动作")
            menu.addSeparator()
            delete_action = menu.addAction("🗑️ 删除")
            
            action = menu.exec(event.globalPos())
            
            if action == set_default_action:
                self.clicked.emit()
            elif action == refresh_action:
                self.refresh_requested.emit()
            elif action == delete_action:
                self.delete_requested.emit()


class Live2DSettingsPage(QWidget):
    """Live2D 设置页面"""
    
    config_changed = Signal()
    model_changed = Signal(str)  # 模型路径变更信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = get_config()
        self._models = []
        self._default_model_index = 0
        self._cards = []
        self._setup_ui()
        self._load_config()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 标题
        title = QLabel("🎭 Live2D 模型配置")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        layout.addWidget(title)
        
        # 提示
        hint = QLabel("点击卡片设为默认模型，右键可删除或刷新动作")
        hint.setStyleSheet("color: #999; font-size: 11px;")
        layout.addWidget(hint)
        
        # 模型卡片区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        self.models_layout = QGridLayout(scroll_content)
        self.models_layout.setSpacing(12)
        self.models_layout.setContentsMargins(5, 5, 5, 5)
        self.models_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll, 1)
        
        # 动作列表区域
        motions_group = QFrame()
        motions_group.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                padding: 5px;
            }
        """)
        motions_layout = QVBoxLayout(motions_group)
        motions_layout.setContentsMargins(15, 15, 15, 15)
        
        motions_title = QLabel("📋 当前模型动作列表")
        motions_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #5c9eff; background: transparent;")
        motions_layout.addWidget(motions_title)
        
        self._motions_list = QListWidget()
        self._motions_list.setStyleSheet("""
            QListWidget {
                background: #f9f9f9;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                font-size: 12px;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:selected {
                background: #e3f2fd;
                color: #333;
            }
        """)
        motions_layout.addWidget(self._motions_list)
        
        layout.addWidget(motions_group)
    
    def _load_config(self):
        """加载配置"""
        # 始终扫描 assets/live2d 目录
        self._scan_models_directory()

        # 如果没有找到模型，从当前配置迁移
        if not self._models:
            current_path = self.config.live2d.model_path
            if current_path:
                valid, name, motions = validate_live2d_model(current_path)
                if valid:
                    self._models = [{
                        'name': name,
                        'path': current_path,
                        'motions': motions
                    }]
                    self._default_model_index = 0

        # 根据配置中的 model_path 确定默认模型
        current_model_path = self.config.live2d.model_path
        if current_model_path:
            for i, model in enumerate(self._models):
                if model.get('path') == current_model_path:
                    self._default_model_index = i
                    break

        self._create_model_cards()
        self._update_motions_list()
    
    def _scan_models_directory(self):
        """扫描 assets/live2d 目录，自动发现模型"""
        self._models = []

        if not ASSETS_LIVE2D_DIR.exists():
            logger.warning(f"模型目录不存在: {ASSETS_LIVE2D_DIR}")
            return

        logger.info(f"扫描模型目录: {ASSETS_LIVE2D_DIR}")

        for model_dir in ASSETS_LIVE2D_DIR.iterdir():
            if model_dir.is_dir() and not model_dir.name.startswith('.'):
                valid, name, motions = validate_live2d_model(str(model_dir))
                if valid:
                    self._models.append({
                        'name': name,
                        'path': str(model_dir),
                        'motions': motions
                    })
                    logger.info(f"模型可用: {name}")

        logger.info(f"扫描到 {len(self._models)} 个模型")
    
    def _create_model_cards(self):
        """创建模型卡片"""
        # 清理现有卡片
        for card in self._cards:
            card.deleteLater()
        self._cards = []
        
        # 清除布局
        while self.models_layout.count():
            item = self.models_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # 添加导入卡片
        add_card = Live2DModelCard({}, is_add_card=True)
        add_card.clicked.connect(self._import_model)
        self.models_layout.addWidget(add_card, 0, 0)
        self._cards.append(add_card)
        
        # 模型卡片
        for i, model in enumerate(self._models):
            is_default = (i == self._default_model_index)
            card = Live2DModelCard(model, is_default=is_default)
            card.clicked.connect(partial(self._set_default_model, i))
            card.delete_requested.connect(partial(self._delete_model, i))
            card.refresh_requested.connect(partial(self._refresh_model, i))
            row = (i + 1) // 3
            col = (i + 1) % 3
            self.models_layout.addWidget(card, row, col)
            self._cards.append(card)
    
    def _update_motions_list(self):
        """更新动作列表"""
        self._motions_list.clear()
        
        if self._models and 0 <= self._default_model_index < len(self._models):
            motions = self._models[self._default_model_index].get('motions', [])
            for motion in motions:
                self._motions_list.addItem(motion)
    
    def _set_default_model(self, index: int):
        """设置默认模型"""
        if index == self._default_model_index:
            return
        
        self._default_model_index = index
        
        # 更新卡片状态（跳过添加卡片）
        model_idx = 0
        for card in self._cards:
            if isinstance(card, Live2DModelCard) and not card.is_add_card:
                card.set_default(model_idx == index)
                model_idx += 1
        
        # 更新动作列表
        self._update_motions_list()
        
        # 立即更新配置中的模型路径
        if 0 <= index < len(self._models):
            model_path = self._models[index].get('path', '')
            self.config.live2d.model_path = model_path
            # 发出模型变更信号
            self.model_changed.emit(model_path)
        
        self.config_changed.emit()
    
    def _import_model(self):
        """导入模型"""
        path = QFileDialog.getExistingDirectory(self, "选择 Live2D 模型目录")
        if not path:
            return

        source_path = Path(path)

        # 检查是否已存在
        for model in self._models:
            existing_path = model.get('path', '')
            # 检查是否是同一个模型（通过名称或路径）
            if existing_path == path or Path(existing_path).name == source_path.name:
                QMessageBox.warning(self, "提示", "该模型已存在")
                return

        # 验证模型
        valid, name, motions = validate_live2d_model(path)

        if not valid:
            QMessageBox.warning(self, "导入失败",
                f"无效的 Live2D 模型目录:\n{path}\n\n请确保目录包含 .model3.json 和 .moc3 文件")
            return

        # 复制模型到 assets/live2d 目录
        try:
            # 确保 assets/live2d 目录存在
            ASSETS_LIVE2D_DIR.mkdir(parents=True, exist_ok=True)

            # 目标路径
            target_path = ASSETS_LIVE2D_DIR / source_path.name

            # 如果目标已存在，添加后缀
            if target_path.exists():
                count = 1
                while (ASSETS_LIVE2D_DIR / f"{source_path.name}_{count}").exists():
                    count += 1
                target_path = ASSETS_LIVE2D_DIR / f"{source_path.name}_{count}"

            # 复制整个目录
            shutil.copytree(source_path, target_path)
            logger.info(f"模型已复制到: {target_path}")

            # 使用相对路径保存
            final_path = get_relative_path(target_path)

        except Exception as e:
            logger.error(f"复制模型失败: {e}")
            QMessageBox.warning(self, "导入失败", f"无法复制模型到 assets 目录:\n{e}")
            return

        # 添加模型
        self._models.append({
            'name': name,
            'path': final_path,
            'motions': motions
        })
        
        # 自动将新导入的模型设为默认
        new_index = len(self._models) - 1
        self._default_model_index = new_index
        
        self._create_model_cards()
        self._update_motions_list()
        
        # 发出模型变更信号
        self.model_changed.emit(final_path)
        self.config_changed.emit()
        
        QMessageBox.information(self, "导入成功", 
            f"模型 \"{name}\" 已导入并设为默认\n可用动作: {len(motions)} 个\n已保存到: {final_path}")
    
    def _delete_model(self, index: int):
        """删除模型"""
        if len(self._models) <= 1:
            QMessageBox.warning(self, "提示", "至少需要保留一个模型")
            return
        
        model_name = self._models[index].get('name', '')
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除模型 \"{model_name}\" 吗？\n\n(仅从列表中移除，不会删除实际文件)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            del self._models[index]
            if self._default_model_index >= len(self._models):
                self._default_model_index = len(self._models) - 1
            self._create_model_cards()
            self._update_motions_list()
            self.config_changed.emit()
    
    def _refresh_model(self, index: int):
        """刷新模型动作"""
        if 0 <= index < len(self._models):
            path = self._models[index].get('path', '')
            valid, name, motions = validate_live2d_model(path)
            
            if valid:
                self._models[index]['motions'] = motions
                self._create_model_cards()
                if index == self._default_model_index:
                    self._update_motions_list()
                QMessageBox.information(self, "刷新成功", 
                    f"已更新 {len(motions)} 个动作")
            else:
                QMessageBox.warning(self, "刷新失败", "模型文件可能已被移动或删除")
    
    def save(self):
        """保存配置"""
        self.config.live2d_models = {
            'models': self._models,
            'default_index': self._default_model_index
        }
        
        if self._models and 0 <= self._default_model_index < len(self._models):
            default_model = self._models[self._default_model_index]
            self.config.live2d.model_path = default_model.get('path', '')
        
        logger.info("Live2D 配置已保存")
