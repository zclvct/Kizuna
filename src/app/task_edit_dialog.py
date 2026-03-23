# Task Edit Dialog
import sys
from pathlib import Path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QComboBox, QMessageBox,
    QSpinBox, QTextEdit
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from scheduler import ScheduledTask
from utils import get_logger

logger = get_logger()


class TaskEditDialog(QDialog):
    """任务编辑对话框"""

    task_updated = Signal()

    def __init__(self, task: ScheduledTask, parent=None):
        super().__init__(parent)
        self.task = task
        self._setup_ui()
        self._load_task_data()

    def _setup_ui(self):
        """设置 UI"""
        self.setWindowTitle("编辑定时任务")
        self.setMinimumSize(500, 450)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.MSWindowsFixedSizeDialogHint)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # 标题
        title = QLabel("✏️ 编辑定时任务")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(title)

        # 任务名称
        layout.addWidget(QLabel("任务名称:"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("例如：每日早报")
        layout.addWidget(self.name_edit)

        # Cron 表达式
        layout.addWidget(QLabel("Cron 表达式 (分 时 日 月 周):"))
        cron_layout = QHBoxLayout()

        self.cron_edit = QLineEdit()
        self.cron_edit.setPlaceholderText("例如: 0 8 * * *")
        cron_layout.addWidget(self.cron_edit)

        build_btn = QPushButton("构建器")
        build_btn.setMaximumWidth(70)
        build_btn.clicked.connect(self._open_cron_builder)
        cron_layout.addWidget(build_btn)

        help_btn = QPushButton("帮助")
        help_btn.setMaximumWidth(60)
        help_btn.clicked.connect(self._show_cron_help)
        cron_layout.addWidget(help_btn)

        layout.addLayout(cron_layout)

        # Cron 预设
        layout.addWidget(QLabel("快速预设:"))
        preset_layout = QHBoxLayout()

        self.daily_btn = QPushButton("每天")
        self.daily_btn.clicked.connect(lambda: self._set_cron_preset("0 8 * * *"))
        preset_layout.addWidget(self.daily_btn)

        self.weekly_btn = QPushButton("每周一")
        self.weekly_btn.clicked.connect(lambda: self._set_cron_preset("0 9 * * 1"))
        preset_layout.addWidget(self.weekly_btn)

        self.hourly_btn = QPushButton("每小时")
        self.hourly_btn.clicked.connect(lambda: self._set_cron_preset("0 * * * *"))
        preset_layout.addWidget(self.hourly_btn)

        preset_layout.addStretch()
        layout.addLayout(preset_layout)

        # 动作提示
        layout.addWidget(QLabel("动作提示 (LLM 执行时收到的指令):"))
        self.prompt_edit = QTextEdit()
        self.prompt_edit.setPlaceholderText("例如: 请整理今天的新闻头条")
        self.prompt_edit.setMaximumHeight(100)
        layout.addWidget(self.prompt_edit)

        # Live2D 动作
        layout.addWidget(QLabel("Live2D 动作 (可选):"))
        motion_layout = QHBoxLayout()

        self.motion_combo = QComboBox()
        self.motion_combo.addItem("(无)", None)
        # 常见的动作预设
        motions = [
            "idle_01", "idle_02",
            "wave", "nod", "smile",
            "thinking_01", "happy_01",
            "sad_01", "angry_01"
        ]
        for motion in motions:
            self.motion_combo.addItem(motion, motion)
        motion_layout.addWidget(self.motion_combo)

        motion_layout.addStretch()
        layout.addLayout(motion_layout)

        # 按钮区
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self._save_task)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

        # 样式
        self.setStyleSheet("""
            QDialog {
                background-color: #F5F5F5;
            }
            QLabel {
                color: #333;
                font-weight: bold;
            }
            QLineEdit, QTextEdit, QComboBox {
                padding: 8px;
                border: 1px solid #E0E0E0;
                border-radius: 6px;
                background-color: white;
                font-size: 13px;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
                border: 2px solid #007AFF;
            }
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #0056CC;
            }
            QPushButton#help_btn {
                background-color: #FF9500;
            }
            QPushButton#preset_btn {
                background-color: #34C759;
            }
        """)

        # 设置按钮样式
        help_btn.setObjectName("help_btn")
        self.daily_btn.setObjectName("preset_btn")
        self.weekly_btn.setObjectName("preset_btn")
        self.hourly_btn.setObjectName("preset_btn")

    def _load_task_data(self):
        """加载任务数据"""
        self.name_edit.setText(self.task.task_name)
        self.cron_edit.setText(self.task.cron)
        self.prompt_edit.setPlainText(self.task.action_prompt)

        # 设置动作选择
        if self.task.motion_id:
            index = self.motion_combo.findData(self.task.motion_id)
            if index >= 0:
                self.motion_combo.setCurrentIndex(index)

    def _set_cron_preset(self, cron: str):
        """设置 Cron 预设"""
        self.cron_edit.setText(cron)

    def _open_cron_builder(self):
        """打开 Cron 构建器"""
        from .cron_builder import CronBuilderDialog

        current_cron = self.cron_edit.text().strip()
        dialog = CronBuilderDialog(current_cron, self)
        dialog.cron_built.connect(self.cron_edit.setText)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            pass  # cron_built 信号已处理

    def _show_cron_help(self):
        """显示 Cron 帮助"""
        help_text = """
Cron 表达式格式: 分 时 日 月 周

字段说明:
  分 (0-59)    - 分钟
  时 (0-23)    - 小时
  日 (1-31)    - 日期
  月 (1-12)    - 月份
  周 (0-6)     - 星期 (0=周日, 6=周六)

特殊符号:
  *    - 任意值
  ,    - 分隔多个值
  -    - 范围 (如 1-5)
  /    - 间隔 (如 */2 表示每2)

示例:
  0 8 * * *      - 每天 8:00
  0 */2 * * *    - 每2小时
  0 9 * * 1-5    - 周一到周五 9:00
  0 0 1 * *      - 每月1号 0:00
  30 8 * * 1     - 每周一 8:30
        """.strip()

        QMessageBox.information(self, "Cron 表达式帮助", help_text)

    def _save_task(self):
        """保存任务"""
        name = self.name_edit.text().strip()
        cron = self.cron_edit.text().strip()
        prompt = self.prompt_edit.toPlainText().strip()
        motion_id = self.motion_combo.currentData()

        # 验证输入
        if not name:
            QMessageBox.warning(self, "验证失败", "请输入任务名称")
            return

        if not cron:
            QMessageBox.warning(self, "验证失败", "请输入 Cron 表达式")
            return

        if len(cron.split()) != 5:
            QMessageBox.warning(self, "验证失败", "Cron 表达式格式不正确")
            return

        if not prompt:
            QMessageBox.warning(self, "验证失败", "请输入动作提示")
            return

        # 更新任务
        self.task.task_name = name
        self.task.cron = cron
        self.task.action_prompt = prompt
        self.task.motion_id = motion_id

        self.task_updated.emit()
        self.accept()

        logger.info(f"已更新任务: {name} ({cron})")
