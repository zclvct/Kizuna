# Task Edit Dialog - 任务编辑对话框
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QTextEdit, QPushButton, QComboBox,
    QMessageBox, QWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from scheduler import get_task_manager
from utils import get_logger

logger = get_logger()


class TaskEditDialog(QDialog):
    """任务编辑对话框"""
    
    def __init__(self, task, parent=None):
        super().__init__(parent)
        self.task = task
        self.task_manager = get_task_manager()
        self._setup_ui()
        self._load_task_data()
    
    def _setup_ui(self):
        """设置 UI"""
        self.setWindowTitle("编辑定时任务")
        self.setMinimumWidth(480)
        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }
            QLabel {
                color: #333;
                font-size: 13px;
            }
            QLineEdit, QTextEdit {
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 8px;
                font-size: 13px;
                background-color: #fafafa;
            }
            QLineEdit:focus, QTextEdit:focus {
                border-color: #5c9eff;
                background-color: white;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 任务名称
        name_layout = QVBoxLayout()
        name_label = QLabel("任务名称")
        name_label.setStyleSheet("font-weight: bold;")
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("输入任务名称")
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)
        
        # 执行时间
        time_layout = QVBoxLayout()
        time_label = QLabel("执行时间 (Cron 表达式)")
        time_label.setStyleSheet("font-weight: bold;")
        
        time_hint = QLabel("示例：0 9 * * * 表示每天 9:00 执行")
        time_hint.setStyleSheet("color: #999; font-size: 11px; font-weight: normal;")
        
        time_input_layout = QHBoxLayout()
        self.cron_edit = QLineEdit()
        self.cron_edit.setPlaceholderText("例如: 0 9 * * *")
        
        # 快捷选择
        self.time_combo = QComboBox()
        self.time_combo.addItem("快捷选择...", "")
        self.time_combo.addItem("每天 9:00", "0 9 * * *")
        self.time_combo.addItem("每天 12:00", "0 12 * * *")
        self.time_combo.addItem("每天 18:00", "0 18 * * *")
        self.time_combo.addItem("每小时", "0 * * * *")
        self.time_combo.addItem("每分钟(测试)", "* * * * *")
        self.time_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 8px;
                min-width: 120px;
                background-color: #fafafa;
            }
            QComboBox:hover {
                border-color: #5c9eff;
            }
        """)
        self.time_combo.currentIndexChanged.connect(self._on_time_selected)
        
        time_input_layout.addWidget(self.cron_edit, 1)
        time_input_layout.addWidget(self.time_combo)
        
        time_layout.addWidget(time_label)
        time_layout.addWidget(time_hint)
        time_layout.addLayout(time_input_layout)
        layout.addLayout(time_layout)
        
        # 任务提示
        prompt_layout = QVBoxLayout()
        prompt_label = QLabel("任务提示")
        prompt_label.setStyleSheet("font-weight: bold;")
        prompt_hint = QLabel("任务执行时 AI 将收到此提示")
        prompt_hint.setStyleSheet("color: #999; font-size: 11px; font-weight: normal;")
        self.prompt_edit = QTextEdit()
        self.prompt_edit.setPlaceholderText("例如：提醒我开会")
        self.prompt_edit.setMaximumHeight(100)
        prompt_layout.addWidget(prompt_label)
        prompt_layout.addWidget(prompt_hint)
        prompt_layout.addWidget(self.prompt_edit)
        layout.addLayout(prompt_layout)
        
        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("取消")
        cancel_btn.setObjectName("secondaryBtn")
        cancel_btn.setMinimumWidth(80)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("保存")
        save_btn.setMinimumWidth(80)
        save_btn.clicked.connect(self._save_task)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #5c9eff;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4a8fe0;
            }
        """)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
    
    def _load_task_data(self):
        """加载任务数据"""
        self.name_edit.setText(self.task.task_name)
        self.cron_edit.setText(self.task.cron)
        self.prompt_edit.setPlainText(self.task.action_prompt)
    
    def _on_time_selected(self, index):
        """快捷时间选择"""
        cron = self.time_combo.currentData()
        if cron:
            self.cron_edit.setText(cron)
    
    def _save_task(self):
        """保存任务"""
        name = self.name_edit.text().strip()
        cron = self.cron_edit.text().strip()
        prompt = self.prompt_edit.toPlainText().strip()
        
        if not name:
            QMessageBox.warning(self, "提示", "请输入任务名称")
            return
        
        if not cron:
            QMessageBox.warning(self, "提示", "请输入执行时间")
            return
        
        if not prompt:
            QMessageBox.warning(self, "提示", "请输入任务提示")
            return
        
        # 验证 Cron 表达式
        try:
            from apscheduler.triggers.cron import CronTrigger
            CronTrigger.from_crontab(cron)
        except Exception as e:
            QMessageBox.warning(self, "提示", f"Cron 表达式格式错误：{str(e)}")
            return
        
        # 更新任务
        self.task.task_name = name
        self.task.cron = cron
        self.task.action_prompt = prompt
        
        # 保存
        self.task_manager.storage.update(self.task)
        
        # 如果任务已启用，更新调度器
        if self.task.enabled and self.task_manager._running:
            try:
                self.task_manager.scheduler.remove_job(self.task.id)
                self.task_manager._add_job(self.task)
            except Exception as e:
                logger.error(f"更新调度器失败: {e}")
        
        logger.info(f"任务已更新: {name}")
        self.accept()
