# Tasks Window
import sys
from pathlib import Path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QLabel,
    QMessageBox, QMenu
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QCursor

from scheduler import TaskManager, get_task_manager
from utils import get_logger

logger = get_logger()


class TasksWindow(QDialog):
    """定时任务管理窗口"""

    def __init__(self, parent=None):
        super().__init__(parent)
        # 设置窗口标志 - 不在任务栏显示
        flags = self.windowFlags()
        flags |= Qt.WindowType.Tool
        self.setWindowFlags(flags)
        
        self.task_manager = get_task_manager()
        self._setup_ui()
        self._load_tasks()

    def _setup_ui(self):
        """设置 UI"""
        self.setWindowTitle("定时任务管理")
        self.setMinimumSize(600, 400)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # 标题
        title = QLabel("📋 定时任务列表")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(title)

        # 任务表格
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "任务名称", "Cron", "动作", "状态", "最后运行", "操作"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        self.table.doubleClicked.connect(self._on_double_click)
        layout.addWidget(self.table, 1)

        # 按钮区
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self._load_tasks)
        btn_layout.addWidget(refresh_btn)

        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

        # 样式
        self.setStyleSheet("""
            TasksWindow {
                background-color: #F5F5F5;
            }
            QTableWidget {
                background-color: white;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                gridline-color: #E0E0E0;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QHeaderView::section {
                background-color: #007AFF;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #0056CC;
            }
        """)

    def _load_tasks(self):
        """加载任务列表"""
        tasks = self.task_manager.list_tasks()
        self.table.setRowCount(len(tasks))

        for row, task in enumerate(tasks):
            # 任务名称
            name_item = QTableWidgetItem(task.task_name)
            name_item.setData(Qt.ItemDataRole.UserRole, task.id)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, name_item)

            # Cron
            cron_item = QTableWidgetItem(task.cron)
            cron_item.setFlags(cron_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 1, cron_item)

            # 动作提示 (截断)
            action_text = task.action_prompt[:30] + "..." if len(task.action_prompt) > 30 else task.action_prompt
            action_item = QTableWidgetItem(action_text)
            action_item.setFlags(action_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 2, action_item)

            # 状态
            status_text = "启用" if task.enabled else "禁用"
            status_item = QTableWidgetItem(status_text)
            status_item.setForeground(Qt.GlobalColor.green if task.enabled else Qt.GlobalColor.gray)
            status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 3, status_item)

            # 最后运行
            last_run_text = task.last_run.strftime("%Y-%m-%d %H:%M") if task.last_run else "-"
            last_run_item = QTableWidgetItem(last_run_text)
            last_run_item.setFlags(last_run_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 4, last_run_item)

            # 操作按钮
            btn_widget = TaskActionButtons(task, self)
            btn_widget.enable_task.connect(self._on_enable_task)
            btn_widget.disable_task.connect(self._on_disable_task)
            btn_widget.edit_task.connect(self._on_edit_task)
            btn_widget.run_now.connect(self._on_run_now)
            btn_widget.delete_task.connect(self._on_delete_task)
            self.table.setCellWidget(row, 5, btn_widget)

    def _show_context_menu(self, pos):
        """显示右键菜单"""
        item = self.table.itemAt(pos)
        if not item:
            return

        row = item.row()
        task_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        task = self.task_manager.storage.get(task_id)
        if not task:
            return

        menu = QMenu(self)

        detail_action = menu.addAction("查看详情")
        detail_action.triggered.connect(lambda: self._on_show_detail(task_id))

        menu.addSeparator()

        edit_action = menu.addAction("编辑")
        edit_action.triggered.connect(lambda: self._on_edit_task(task_id))

        menu.addSeparator()

        if task.enabled:
            disable_action = menu.addAction("禁用")
            disable_action.triggered.connect(lambda: self._on_disable_task(task_id))
        else:
            enable_action = menu.addAction("启用")
            enable_action.triggered.connect(lambda: self._on_enable_task(task_id))

        menu.addSeparator()

        run_now_action = menu.addAction("立即执行")
        run_now_action.triggered.connect(lambda: self._on_run_now(task_id))

        menu.addSeparator()
        delete_action = menu.addAction("删除")
        delete_action.triggered.connect(lambda: self._on_delete_task(task_id))

        menu.exec(QCursor.pos())

    def _on_enable_task(self, task_id: str):
        """启用任务"""
        self.task_manager.enable_task(task_id)
        self._load_tasks()
        logger.info(f"已启用任务: {task_id}")

    def _on_disable_task(self, task_id: str):
        """禁用任务"""
        self.task_manager.disable_task(task_id)
        self._load_tasks()
        logger.info(f"已禁用任务: {task_id}")

    def _on_delete_task(self, task_id: str):
        """删除任务"""
        reply = QMessageBox.question(
            self, "确认删除",
            "确定要删除这个定时任务吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.task_manager.delete_task(task_id)
            self._load_tasks()
            logger.info(f"已删除任务: {task_id}")

    def _on_double_click(self, index):
        """双击事件"""
        row = index.row()
        task_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        self._on_show_detail(task_id)

    def _on_show_detail(self, task_id: str):
        """查看任务详情"""
        from task_detail_dialog import TaskDetailDialog

        task = self.task_manager.storage.get(task_id)
        if not task:
            return

        dialog = TaskDetailDialog(task, self)
        dialog.task_edited.connect(self._load_tasks)
        dialog.exec()

    def _on_edit_task(self, task_id: str):
        """编辑任务"""
        from task_edit_dialog import TaskEditDialog

        task = self.task_manager.storage.get(task_id)
        if not task:
            return

        dialog = TaskEditDialog(task, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # 更新任务
            self.task_manager.storage.update(task)
            # 如果任务启用,重新调度
            if task.enabled:
                self.task_manager._add_job(task)
            self._load_tasks()
            logger.info(f"已编辑任务: {task.task_name}")

    def _on_run_now(self, task_id: str):
        """立即执行任务"""
        task = self.task_manager.storage.get(task_id)
        if not task:
            return

        reply = QMessageBox.question(
            self, "确认执行",
            f"确定要立即执行任务「{task.task_name}」吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            # 触发任务执行
            import asyncio
            asyncio.create_task(self.task_manager._execute_task(task_id))
            logger.info(f"已手动触发任务: {task.task_name}")
            QMessageBox.information(self, "执行中", "任务已在后台开始执行")


from PySide6.QtWidgets import QWidget, QPushButton, QHBoxLayout


class TaskActionButtons(QWidget):
    """任务操作按钮组"""

    enable_task = Signal(str)
    disable_task = Signal(str)
    delete_task = Signal(str)
    edit_task = Signal(str)
    run_now = Signal(str)

    def __init__(self, task, parent=None):
        super().__init__(parent)
        self.task_id = task.id
        self._task = task
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(3)

        # 启用/禁用按钮
        if self._task.enabled:
            self.toggle_btn = QPushButton("停")
            self.toggle_btn.setMaximumWidth(30)
            self.toggle_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FF9500;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    padding: 2px 4px;
                    font-size: 10px;
                }
                QPushButton:hover {
                    background-color: #E08500;
                }
            """)
            self.toggle_btn.clicked.connect(lambda: self.disable_task.emit(self.task_id))
        else:
            self.toggle_btn = QPushButton("启")
            self.toggle_btn.setMaximumWidth(30)
            self.toggle_btn.setStyleSheet("""
                QPushButton {
                    background-color: #34C759;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    padding: 2px 4px;
                    font-size: 10px;
                }
                QPushButton:hover {
                    background-color: #28A745;
                }
            """)
            self.toggle_btn.clicked.connect(lambda: self.enable_task.emit(self.task_id))

        layout.addWidget(self.toggle_btn)

        # 编辑按钮
        edit_btn = QPushButton("编辑")
        edit_btn.setMaximumWidth(40)
        edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 2px 4px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #0056CC;
            }
        """)
        edit_btn.clicked.connect(lambda: self.edit_task.emit(self.task_id))
        layout.addWidget(edit_btn)

        # 立即执行按钮
        run_btn = QPushButton("运行")
        run_btn.setMaximumWidth(40)
        run_btn.setStyleSheet("""
            QPushButton {
                background-color: #5856D6;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 2px 4px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #4A48B5;
            }
        """)
        run_btn.clicked.connect(lambda: self.run_now.emit(self.task_id))
        layout.addWidget(run_btn)

        # 删除按钮
        delete_btn = QPushButton("删除")
        delete_btn.setMaximumWidth(40)
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF3B30;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 2px 4px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #E0352B;
            }
        """)
        delete_btn.clicked.connect(lambda: self.delete_task.emit(self.task_id))
        layout.addWidget(delete_btn)

