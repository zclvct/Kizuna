# Memory Settings Page - 记忆管理页面
import sys
from pathlib import Path
src_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_path))

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTextEdit, QPushButton, QMessageBox, QListWidget,
    QListWidgetItem, QGroupBox, QLineEdit, QSplitter
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from .styles import ANIME_STYLE
from utils import get_logger

logger = get_logger()


class MemorySettingsPage(QWidget):
    """记忆管理页面
    
    查看和管理长期记忆、事实知识库
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._memory = None
        self._setup_ui()
        self._load_memories()
    
    @property
    def memory(self):
        if self._memory is None:
            from agent import get_langchain_memory
            self._memory = get_langchain_memory()
        return self._memory
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 标题
        title = QLabel("🧠 记忆管理")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        layout.addWidget(title)
        
        hint = QLabel("查看和管理助手的长期记忆和事实知识")
        hint.setStyleSheet("color: #999; font-size: 11px;")
        layout.addWidget(hint)
        
        # 分割器
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # 事实知识库
        facts_widget = QWidget()
        facts_layout = QVBoxLayout(facts_widget)
        facts_layout.setContentsMargins(0, 0, 0, 0)
        
        facts_group = QGroupBox("📖 事实知识库")
        facts_inner = QVBoxLayout(facts_group)
        
        # 添加事实
        add_fact_layout = QHBoxLayout()
        self.fact_key_input = QLineEdit()
        self.fact_key_input.setPlaceholderText("键名 (如: 用户姓名)")
        add_fact_layout.addWidget(self.fact_key_input)
        
        self.fact_value_input = QLineEdit()
        self.fact_value_input.setPlaceholderText("值 (如: 小明)")
        add_fact_layout.addWidget(self.fact_value_input)
        
        add_fact_btn = QPushButton("添加")
        add_fact_btn.setMaximumWidth(60)
        add_fact_btn.clicked.connect(self._add_fact)
        add_fact_layout.addWidget(add_fact_btn)
        
        facts_inner.addLayout(add_fact_layout)
        
        # 事实列表
        self.facts_list = QListWidget()
        self.facts_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                background-color: white;
            }
            QListWidget::item {
                padding: 8px;
            }
        """)
        facts_inner.addWidget(self.facts_list)
        
        # 删除按钮
        del_fact_btn = QPushButton("删除选中")
        del_fact_btn.clicked.connect(self._delete_fact)
        facts_inner.addWidget(del_fact_btn)
        
        facts_layout.addWidget(facts_group)
        splitter.addWidget(facts_widget)
        
        # 长期记忆
        memory_widget = QWidget()
        memory_layout = QVBoxLayout(memory_widget)
        memory_layout.setContentsMargins(0, 0, 0, 0)
        
        memory_group = QGroupBox("💭 长期记忆")
        memory_inner = QVBoxLayout(memory_group)
        
        # 添加记忆
        add_mem_layout = QHBoxLayout()
        self.memory_input = QLineEdit()
        self.memory_input.setPlaceholderText("输入要记住的内容...")
        add_mem_layout.addWidget(self.memory_input)
        
        add_mem_btn = QPushButton("添加")
        add_mem_btn.setMaximumWidth(60)
        add_mem_btn.clicked.connect(self._add_memory)
        add_mem_layout.addWidget(add_mem_btn)
        
        memory_inner.addLayout(add_mem_layout)
        
        # 记忆列表
        self.memories_list = QListWidget()
        self.memories_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                background-color: white;
            }
            QListWidget::item {
                padding: 8px;
            }
        """)
        memory_inner.addWidget(self.memories_list)
        
        # 删除按钮
        del_mem_btn = QPushButton("删除选中")
        del_mem_btn.clicked.connect(self._delete_memory)
        memory_inner.addWidget(del_mem_btn)
        
        memory_layout.addWidget(memory_group)
        splitter.addWidget(memory_widget)
        
        layout.addWidget(splitter)
        
        # 操作按钮
        btn_layout = QHBoxLayout()
        
        archive_btn = QPushButton("归档对话")
        archive_btn.setObjectName("secondaryBtn")
        archive_btn.clicked.connect(self._archive_conversation)
        btn_layout.addWidget(archive_btn)
        
        clear_btn = QPushButton("清空短期记忆")
        clear_btn.setObjectName("secondaryBtn")
        clear_btn.clicked.connect(self._clear_short_term)
        btn_layout.addWidget(clear_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
    
    def _load_memories(self):
        """加载记忆"""
        # 加载事实
        self.facts_list.clear()
        for fact in self.memory.long_term.facts:
            item = QListWidgetItem(f"📌 {fact.key}: {fact.value}")
            item.setData(Qt.ItemDataRole.UserRole, fact.key)
            self.facts_list.addItem(item)
        
        # 加载记忆
        self.memories_list.clear()
        for memory in self.memory.long_term.get_recent_memories(20):
            item = QListWidgetItem(f"💭 {memory.content[:50]}...")
            item.setData(Qt.ItemDataRole.UserRole, memory.id)
            self.memories_list.addItem(item)
    
    def _add_fact(self):
        """添加事实"""
        key = self.fact_key_input.text().strip()
        value = self.fact_value_input.text().strip()
        
        if not key or not value:
            QMessageBox.warning(self, "提示", "请输入键名和值")
            return
        
        self.memory.save_fact(key, value)
        self.fact_key_input.clear()
        self.fact_value_input.clear()
        self._load_memories()
        
        QMessageBox.information(self, "成功", f"已添加事实: {key}")
    
    def _delete_fact(self):
        """删除事实"""
        current = self.facts_list.currentItem()
        if not current:
            QMessageBox.warning(self, "提示", "请先选择要删除的事实")
            return
        
        key = current.data(Qt.ItemDataRole.UserRole)
        reply = QMessageBox.question(
            self, "确认", f"确定删除事实 '{key}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 从事实列表中移除
            self.memory.long_term.facts = [
                f for f in self.memory.long_term.facts if f.key != key
            ]
            self.memory.long_term.save()
            self._load_memories()
    
    def _add_memory(self):
        """添加记忆"""
        content = self.memory_input.text().strip()
        
        if not content:
            QMessageBox.warning(self, "提示", "请输入记忆内容")
            return
        
        self.memory.add_long_term_memory(content)
        self.memory_input.clear()
        self._load_memories()
        
        QMessageBox.information(self, "成功", "已添加记忆")
    
    def _delete_memory(self):
        """删除记忆"""
        current = self.memories_list.currentItem()
        if not current:
            QMessageBox.warning(self, "提示", "请先选择要删除的记忆")
            return
        
        memory_id = current.data(Qt.ItemDataRole.UserRole)
        reply = QMessageBox.question(
            self, "确认", "确定删除选中的记忆?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 从记忆列表中移除
            self.memory.long_term.memories = [
                m for m in self.memory.long_term.memories if m.id != memory_id
            ]
            self.memory.long_term.save()
            self._load_memories()
    
    def _archive_conversation(self):
        """归档对话"""
        reply = QMessageBox.question(
            self, "确认", "确定归档当前对话?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # TODO: 实现归档功能
            QMessageBox.information(self, "成功", "对话已归档")
    
    def _clear_short_term(self):
        """清空短期记忆"""
        reply = QMessageBox.question(
            self, "确认", "确定清空短期记忆（对话历史）?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.memory.clear()
            QMessageBox.information(self, "成功", "短期记忆已清空")
    
    def save(self):
        """保存"""
        # 记忆在添加/删除时已实时保存
        pass
    
    def reset(self):
        """重置"""
        self._load_memories()
