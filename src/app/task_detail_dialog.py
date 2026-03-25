# Task Detail Dialog
import sys
from pathlib import Path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QGroupBox, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from scheduler import ScheduledTask, get_task_history_manager
from utils import get_logger

logger = get_logger()


class TaskDetailDialog(QDialog):
    """任务详情对话框"""

    task_edited = Signal()

    def __init__(self, task: ScheduledTask, parent=None):
        super().__init__(parent)
        self.task = task
        self.history_manager = get_task_history_manager()
        self._setup_ui()
        self._load_task_info()
        self._load_history()

    def _setup_ui(self):
        """设置 UI"""
        self.setWindowTitle("任务详情")
        self.setMinimumSize(700, 600)
        # 设置窗口标志 - 不在任务栏显示
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.MSWindowsFixedSizeDialogHint | Qt.WindowType.Tool)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # 标题
        title = QLabel(f"📋 {self.task.task_name}")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        layout.addWidget(title)

        # 任务基本信息
        info_group = QGroupBox("基本信息")
        info_layout = QVBoxLayout()

        # ID
        id_row = QHBoxLayout()
        id_row.addWidget(QLabel("ID:"))
        id_label = QLabel(self.task.id[:8] + "...")
        id_label.setStyleSheet("color: #666; font-family: monospace;")
        id_row.addWidget(id_label)
        id_row.addStretch()
        info_layout.addLayout(id_row)

        # Cron
        cron_row = QHBoxLayout()
        cron_row.addWidget(QLabel("Cron:"))
        cron_label = QLabel(self.task.cron)
        cron_label.setStyleSheet("color: #007AFF; font-weight: bold; font-family: monospace;")
        cron_row.addWidget(cron_label)
        cron_row.addStretch()
        info_layout.addLayout(cron_row)

        # 动作提示
        prompt_label = QLabel("动作提示:")
        info_layout.addWidget(prompt_label)
        prompt_text = QLabel(self.task.action_prompt)
        prompt_text.setWordWrap(True)
        prompt_text.setStyleSheet(
            "color: #333; padding: 10px; background-color: #F5F5F5; "
            "border-radius: 6px; border: 1px solid #E0E0E0;"
        )
        info_layout.addWidget(prompt_text)

        # Live2D 动作
        if self.task.motion_id:
            motion_row = QHBoxLayout()
            motion_row.addWidget(QLabel("Live2D 动作:"))
            motion_label = QLabel(self.task.motion_id)
            motion_label.setStyleSheet("color: #FF9500; font-weight: bold;")
            motion_row.addWidget(motion_label)
            motion_row.addStretch()
            info_layout.addLayout(motion_row)

        # 状态和时间
        status_layout = QHBoxLayout()

        status_layout.addWidget(QLabel("状态:"))
        status_text = "启用" if self.task.enabled else "禁用"
        status_label = QLabel(status_text)
        status_label.setStyleSheet(
            f"color: #34C759; font-weight: bold;" if self.task.enabled
            else "color: #8E8E93; font-weight: bold;"
        )
        status_layout.addWidget(status_label)

        status_layout.addWidget(QLabel("  创建时间:"))
        created_label = QLabel(self.task.created_at.strftime("%Y-%m-%d %H:%M"))
        status_layout.addWidget(created_label)

        if self.task.last_run:
            status_layout.addWidget(QLabel("  最后运行:"))
            last_run_label = QLabel(self.task.last_run.strftime("%Y-%m-%d %H:%M"))
            status_layout.addWidget(last_run_label)

        status_layout.addStretch()
        info_layout.addLayout(status_layout)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # 统计信息
        stats_group = QGroupBox("执行统计")
        stats_layout = QHBoxLayout()

        stats = self.history_manager.get_statistics(self.task.id)

        self.total_label = QLabel(f"总执行: {stats['total_executions']} 次")
        stats_layout.addWidget(self.total_label)

        self.success_label = QLabel(f"成功: {stats['success_count']} 次")
        self.success_label.setStyleSheet("color: #34C759; font-weight: bold;")
        stats_layout.addWidget(self.success_label)

        self.failure_label = QLabel(f"失败: {stats['failure_count']} 次")
        self.failure_label.setStyleSheet("color: #FF3B30; font-weight: bold;")
        stats_layout.addWidget(self.failure_label)

        if stats['average_duration']:
            duration_label = QLabel(f"平均耗时: {stats['average_duration']} 秒")
            stats_layout.addWidget(duration_label)

        stats_layout.addStretch()
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        # 执行历史
        history_group = QGroupBox("执行历史 (最近 20 条)")
        history_layout = QVBoxLayout()

        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels([
            "执行时间", "状态", "结果", "错误", "耗时(秒)"
        ])
        self.history_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.history_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.history_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.history_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.history_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.history_table.setAlternatingRowColors(True)
        self.history_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        history_layout.addWidget(self.history_table)

        history_group.setLayout(history_layout)
        layout.addWidget(history_group, 1)

        # 按钮区
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.clicked.connect(self._refresh)
        btn_layout.addWidget(self.refresh_btn)

        self.edit_btn = QPushButton("编辑")
        self.edit_btn.clicked.connect(self._edit_task)
        btn_layout.addWidget(self.edit_btn)

        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

        # 样式
        self.setStyleSheet("""
            QDialog {
                background-color: #F5F5F5;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QLabel {
                color: #333;
            }
            QTableWidget {
                background-color: white;
                border: 1px solid #E0E0E0;
                border-radius: 6px;
                gridline-color: #E0E0E0;
            }
            QTableWidget::item {
                padding: 6px;
            }
            QHeaderView::section {
                background-color: #007AFF;
                color: white;
                padding: 6px;
                border: none;
                font-weight: bold;
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
        """)

    def _load_task_info(self):
        """加载任务信息"""
        # 已经在构造函数中加载
        pass

    def _load_history(self):
        """加载执行历史"""
        records = self.history_manager.get_task_history(self.task.id, limit=20)
        self.history_table.setRowCount(len(records))

        for row, record in enumerate(records):
            # 执行时间
            time_text = record.executed_at.strftime("%Y-%m-%d %H:%M:%S")
            time_item = QTableWidgetItem(time_text)
            time_item.setFlags(time_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.history_table.setItem(row, 0, time_item)

            # 状态
            status_text = "成功" if record.success else "失败"
            status_item = QTableWidgetItem(status_text)
            status_item.setForeground(Qt.GlobalColor.green if record.success else Qt.GlobalColor.red)
            status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.history_table.setItem(row, 1, status_item)

            # 结果
            result_text = record.result or "-"
            if len(result_text) > 50:
                result_text = result_text[:50] + "..."
            result_item = QTableWidgetItem(result_text)
            result_item.setFlags(result_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.history_table.setItem(row, 2, result_item)

            # 错误
            error_text = record.error or "-"
            if len(error_text) > 50:
                error_text = error_text[:50] + "..."
            error_item = QTableWidgetItem(error_text)
            error_item.setForeground(Qt.GlobalColor.red if record.error else Qt.GlobalColor.gray)
            error_item.setFlags(error_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.history_table.setItem(row, 3, error_item)

            # 耗时
            duration_text = f"{record.duration_seconds:.2f}" if record.duration_seconds else "-"
            duration_item = QTableWidgetItem(duration_text)
            duration_item.setFlags(duration_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.history_table.setItem(row, 4, duration_item)

    def _refresh(self):
        """刷新"""
        self._load_history()

        # 更新统计
        stats = self.history_manager.get_statistics(self.task.id)
        self.total_label.setText(f"总执行: {stats['total_executions']} 次")
        self.success_label.setText(f"成功: {stats['success_count']} 次")
        self.failure_label.setText(f"失败: {stats['failure_count']} 次")

    def _edit_task(self):
        """编辑任务"""
        from .task_edit_dialog import TaskEditDialog

        dialog = TaskEditDialog(self.task, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.task_edited.emit()
            self._load_task_info()
            logger.info(f"任务已编辑: {self.task.task_name}")
