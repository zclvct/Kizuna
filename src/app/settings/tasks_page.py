# Tasks Settings Page - 定时任务设置页面
import sys
from pathlib import Path
src_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_path))

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QSplitter, QMessageBox, QMenu, QFrame
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QCursor, QColor

from scheduler import get_task_manager, get_task_history_manager
from utils import get_logger

logger = get_logger()


class TasksSettingsPage(QWidget):
    """定时任务设置页面"""
    
    task_updated = Signal()  # 任务更新信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.task_manager = get_task_manager()
        self.history_manager = get_task_history_manager()
        self._setup_ui()
        self._load_tasks()
        self._load_history()
    
    def _setup_ui(self):
        """设置 UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 使用 QSplitter 分隔任务列表和历史记录
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # ========== 上半部分：任务列表 ==========
        tasks_widget = QWidget()
        tasks_layout = QVBoxLayout(tasks_widget)
        tasks_layout.setContentsMargins(10, 10, 10, 10)
        tasks_layout.setSpacing(8)
        
        # 标题
        title_layout = QHBoxLayout()
        title = QLabel("⏰ 定时任务")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        title_layout.addWidget(title)
        title_layout.addStretch()
        
        # 刷新按钮
        refresh_btn = QPushButton("刷新")
        refresh_btn.setObjectName("secondaryBtn")
        refresh_btn.setMaximumWidth(80)
        refresh_btn.clicked.connect(self._refresh_all)
        title_layout.addWidget(refresh_btn)
        
        tasks_layout.addLayout(title_layout)
        
        # 提示信息
        hint = QLabel("💡 通过对话创建任务：对助手说 \"每天10点提醒我开会\"")
        hint.setStyleSheet("color: #999; font-size: 11px; padding: 5px;")
        tasks_layout.addWidget(hint)
        
        # 任务表格
        self.tasks_table = QTableWidget()
        self.tasks_table.setColumnCount(5)
        self.tasks_table.setHorizontalHeaderLabels([
            "任务名称", "执行时间", "任务提示", "状态", "操作"
        ])
        
        # 设置列宽
        header = self.tasks_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(4, 160)  # 操作列固定宽度（图标按钮）
        
        # 表格样式
        self.tasks_table.setAlternatingRowColors(True)
        self.tasks_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tasks_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tasks_table.customContextMenuRequested.connect(self._show_context_menu)
        self.tasks_table.verticalHeader().setDefaultSectionSize(42)  # 设置行高
        self.tasks_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                gridline-color: #f0f0f0;
            }
            QTableWidget::item {
                padding: 6px;
            }
            QTableWidget::item:selected {
                background-color: #e8f4ff;
                color: #333;
            }
            QHeaderView::section {
                background-color: #5c9eff;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)
        
        tasks_layout.addWidget(self.tasks_table)
        splitter.addWidget(tasks_widget)
        
        # ========== 下半部分：执行历史 ==========
        history_widget = QWidget()
        history_layout = QVBoxLayout(history_widget)
        history_layout.setContentsMargins(10, 10, 10, 10)
        history_layout.setSpacing(8)
        
        # 标题
        history_title_layout = QHBoxLayout()
        history_title = QLabel("📊 执行历史")
        history_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        history_title_layout.addWidget(history_title)
        history_title_layout.addStretch()
        
        # 清理历史按钮
        clear_btn = QPushButton("清理历史")
        clear_btn.setObjectName("secondaryBtn")
        clear_btn.setMaximumWidth(100)
        clear_btn.clicked.connect(self._clear_history)
        history_title_layout.addWidget(clear_btn)
        
        history_layout.addLayout(history_title_layout)
        
        # 历史表格
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels([
            "执行时间", "任务名称", "结果", "耗时", "错误"
        ])
        
        # 设置列宽
        history_header = self.history_table.horizontalHeader()
        history_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        history_header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        history_header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        history_header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        history_header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        
        # 历史表格样式
        self.history_table.setAlternatingRowColors(True)
        self.history_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.history_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                gridline-color: #f0f0f0;
            }
            QTableWidget::item {
                padding: 6px;
            }
            QTableWidget::item:selected {
                background-color: #e8f4ff;
                color: #333;
            }
            QHeaderView::section {
                background-color: #5c9eff;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)
        
        history_layout.addWidget(self.history_table)
        splitter.addWidget(history_widget)
        
        # 设置分割器比例
        splitter.setSizes([300, 200])
        
        main_layout.addWidget(splitter)
    
    def _load_tasks(self):
        """加载任务列表"""
        tasks = self.task_manager.list_tasks()
        self.tasks_table.setRowCount(len(tasks))
        
        for row, task in enumerate(tasks):
            # 任务名称
            name_item = QTableWidgetItem(task.task_name)
            name_item.setData(Qt.ItemDataRole.UserRole, task.id)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            name_item.setForeground(QColor("#333"))
            self.tasks_table.setItem(row, 0, name_item)
            
            # Cron 时间
            cron_text = self._format_cron(task.cron)
            cron_item = QTableWidgetItem(cron_text)
            cron_item.setFlags(cron_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            cron_item.setForeground(QColor("#666"))
            cron_item.setToolTip(f"Cron: {task.cron}")
            self.tasks_table.setItem(row, 1, cron_item)
            
            # 任务提示 (截断)
            prompt_text = task.action_prompt[:40] + "..." if len(task.action_prompt) > 40 else task.action_prompt
            prompt_item = QTableWidgetItem(prompt_text)
            prompt_item.setFlags(prompt_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            prompt_item.setForeground(QColor("#666"))
            prompt_item.setToolTip(task.action_prompt)
            self.tasks_table.setItem(row, 2, prompt_item)
            
            # 状态
            if task.enabled:
                status_item = QTableWidgetItem("✓ 启用")
                status_item.setForeground(QColor("#34C759"))
            else:
                status_item = QTableWidgetItem("○ 禁用")
                status_item.setForeground(QColor("#999"))
            status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.tasks_table.setItem(row, 3, status_item)
            
            # 操作按钮
            action_widget = TaskActionButtons(task, self)
            action_widget.toggle_clicked.connect(self._on_toggle_task)
            action_widget.run_clicked.connect(self._on_run_task)
            action_widget.edit_clicked.connect(self._on_edit_task)
            action_widget.delete_clicked.connect(self._on_delete_task)
            self.tasks_table.setCellWidget(row, 4, action_widget)
    
    def _format_cron(self, cron: str) -> str:
        """格式化 Cron 表达式为易读文本"""
        try:
            parts = cron.split()
            if len(parts) != 5:
                return cron
            
            minute, hour, day, month, weekday = parts
            
            # 常见模式识别
            if minute == "0" and hour != "*" and day == "*" and month == "*" and weekday == "*":
                return f"每天 {hour}:00"
            elif minute == "0" and hour != "*" and day == "*" and month == "*" and weekday != "*":
                weekdays = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"]
                return f"每{weekdays[int(weekday)]} {hour}:00"
            elif minute == "0" and hour == "*" and day == "*" and month == "*" and weekday == "*":
                return "每小时"
            else:
                return cron
        except:
            return cron
    
    def _load_history(self):
        """加载执行历史"""
        records = self.history_manager.get_all_history(limit=50)
        self.history_table.setRowCount(len(records))
        
        for row, record in enumerate(records):
            # 执行时间
            time_text = record.executed_at.strftime("%m-%d %H:%M")
            time_item = QTableWidgetItem(time_text)
            time_item.setFlags(time_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.history_table.setItem(row, 0, time_item)
            
            # 任务名称
            name_item = QTableWidgetItem(record.task_name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.history_table.setItem(row, 1, name_item)
            
            # 结果
            if record.success:
                result_item = QTableWidgetItem("✓ 成功")
                result_item.setForeground(QColor("#34C759"))
            else:
                result_item = QTableWidgetItem("✗ 失败")
                result_item.setForeground(QColor("#FF3B30"))
            result_item.setFlags(result_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.history_table.setItem(row, 2, result_item)
            
            # 耗时
            if record.duration_seconds:
                duration_text = f"{record.duration_seconds:.2f}s"
            else:
                duration_text = "-"
            duration_item = QTableWidgetItem(duration_text)
            duration_item.setFlags(duration_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.history_table.setItem(row, 3, duration_item)
            
            # 错误信息
            error_text = record.error[:50] + "..." if record.error and len(record.error) > 50 else (record.error or "-")
            error_item = QTableWidgetItem(error_text)
            error_item.setFlags(error_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            if record.error:
                error_item.setForeground(QColor("#FF3B30"))
                error_item.setToolTip(record.error)
            self.history_table.setItem(row, 4, error_item)
    
    def _show_context_menu(self, pos):
        """显示右键菜单"""
        item = self.tasks_table.itemAt(pos)
        if not item:
            return
        
        row = item.row()
        task_id = self.tasks_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        task = self.task_manager.storage.get(task_id)
        if not task:
            return
        
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 6px;
            }
            QMenu::item {
                padding: 8px 16px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #e8f4ff;
            }
        """)
        
        # 立即执行
        run_action = menu.addAction("▶ 立即执行（测试）")
        run_action.triggered.connect(lambda: self._on_run_task(task_id))
        
        menu.addSeparator()
        
        # 编辑
        edit_action = menu.addAction("✎ 编辑任务")
        edit_action.triggered.connect(lambda: self._on_edit_task(task_id))
        
        menu.addSeparator()
        
        # 启用/禁用
        if task.enabled:
            disable_action = menu.addAction("○ 禁用任务")
            disable_action.triggered.connect(lambda: self._on_toggle_task(task_id, False))
        else:
            enable_action = menu.addAction("✓ 启用任务")
            enable_action.triggered.connect(lambda: self._on_toggle_task(task_id, True))
        
        menu.addSeparator()
        
        # 删除
        delete_action = menu.addAction("🗑 删除任务")
        delete_action.triggered.connect(lambda: self._on_delete_task(task_id))
        
        menu.exec(QCursor.pos())
    
    def _on_toggle_task(self, task_id: str, enable: bool):
        """启用/禁用任务"""
        task = self.task_manager.storage.get(task_id)
        if not task:
            return

        task.enabled = enable
        self.task_manager.storage.update(task)

        # 如果任务管理器正在运行，更新调度器
        if self.task_manager._running:
            if enable:
                self.task_manager._add_job(task)
            else:
                try:
                    self.task_manager.scheduler.remove_job(task_id)
                except Exception:
                    pass

        status = "启用" if enable else "禁用"
        logger.info(f"已{status}任务: {task.task_name}")
        self._refresh_all()

    def _on_edit_task(self, task_id: str):
        """编辑任务"""
        from app.task_edit_dialog import TaskEditDialog
        
        task = self.task_manager.storage.get(task_id)
        if not task:
            return
        
        dialog = TaskEditDialog(task, self)
        if dialog.exec():
            self._refresh_all()

    def _on_run_task(self, task_id: str):
        """立即执行任务（测试）"""
        task = self.task_manager.storage.get(task_id)
        if not task:
            return

        # 确认对话框
        reply = QMessageBox.question(
            self,
            "确认执行",
            f"确定要立即执行任务「{task.task_name}」吗？\n\n"
            f"任务提示：{task.action_prompt}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # 使用 QTimer 在主线程中触发任务执行
            # 这样可以避免 asyncio 事件循环问题
            QTimer.singleShot(100, lambda: self._execute_task_async(task_id))
            logger.info(f"手动触发任务: {task.task_name}")

            QMessageBox.information(
                self,
                "执行中",
                f"任务「{task.task_name}」已开始执行\n"
                f"请查看对话窗口查看执行结果"
            )

            # 延迟刷新历史记录
            QTimer.singleShot(3000, self._load_history)

    def _execute_task_async(self, task_id: str):
        """异步执行任务"""
        import asyncio

        # 尝试获取现有事件循环
        try:
            loop = asyncio.get_running_loop()
            # 如果有运行中的循环，创建任务
            asyncio.create_task(self.task_manager._execute_task(task_id))
        except RuntimeError:
            # 没有运行中的循环，创建新循环运行
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self.task_manager._execute_task(task_id))
            finally:
                loop.close()

    def _on_delete_task(self, task_id: str):
        """删除任务"""
        task = self.task_manager.storage.get(task_id)
        if not task:
            return

        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除任务「{task.task_name}」吗？\n此操作不可撤销。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # 从调度器移除
            if self.task_manager._running:
                try:
                    self.task_manager.scheduler.remove_job(task_id)
                except Exception:
                    pass

            # 从存储中删除
            self.task_manager.storage.delete(task_id)
            logger.info(f"已删除任务: {task.task_name}")
            self._refresh_all()
    
    def _clear_history(self):
        """清理历史记录"""
        reply = QMessageBox.question(
            self,
            "确认清理",
            "确定要清理 30 天前的执行记录吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.history_manager.clear_old_records(days=30)
            self._load_history()
            logger.info("已清理 30 天前的执行记录")
    
    def _refresh_all(self):
        """刷新所有数据"""
        self._load_tasks()
        self._load_history()
    
    def save(self):
        """保存（此页面无需保存操作）"""
        pass


class TaskActionButtons(QWidget):
    """任务操作按钮组 - 使用图标按钮"""

    toggle_clicked = Signal(str, bool)  # task_id, enable
    run_clicked = Signal(str)  # task_id
    edit_clicked = Signal(str)  # task_id
    delete_clicked = Signal(str)  # task_id

    def __init__(self, task, parent=None):
        super().__init__(parent)
        self.task_id = task.id
        self._task = task
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(4)

        # 图标按钮通用样式
        icon_btn_style = """
            QPushButton {{
                background-color: {bg};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 10px;
                font-size: 12px;
                min-width: 32px;
                max-width: 50px;
            }}
            QPushButton:hover {{
                background-color: {hover};
            }}
            QPushButton:pressed {{
                background-color: {press};
            }}
        """

        # 启用/禁用按钮（图标）
        if self._task.enabled:
            self.toggle_btn = QPushButton("⏸")
            self.toggle_btn.setToolTip("禁用任务")
            self.toggle_btn.setStyleSheet(icon_btn_style.format(
                bg="#FF9500", hover="#E08500", press="#C07500"
            ))
            self.toggle_btn.clicked.connect(lambda: self.toggle_clicked.emit(self.task_id, False))
        else:
            self.toggle_btn = QPushButton("▶")
            self.toggle_btn.setToolTip("启用任务")
            self.toggle_btn.setStyleSheet(icon_btn_style.format(
                bg="#34C759", hover="#28A745", press="#1E8C38"
            ))
            self.toggle_btn.clicked.connect(lambda: self.toggle_clicked.emit(self.task_id, True))

        layout.addWidget(self.toggle_btn)

        # 编辑按钮
        edit_btn = QPushButton("✎")
        edit_btn.setToolTip("编辑任务")
        edit_btn.setStyleSheet(icon_btn_style.format(
            bg="#5c9eff", hover="#4a8fe0", press="#3a7fd0"
        ))
        edit_btn.clicked.connect(lambda: self.edit_clicked.emit(self.task_id))
        layout.addWidget(edit_btn)

        # 立即执行按钮
        run_btn = QPushButton("▶▶")
        run_btn.setToolTip("立即执行（测试）")
        run_btn.setStyleSheet(icon_btn_style.format(
            bg="#5856D6", hover="#4A48B5", press="#3A38A5"
        ))
        run_btn.clicked.connect(lambda: self.run_clicked.emit(self.task_id))
        layout.addWidget(run_btn)

        # 删除按钮
        delete_btn = QPushButton("✕")
        delete_btn.setToolTip("删除任务")
        delete_btn.setStyleSheet(icon_btn_style.format(
            bg="#FF3B30", hover="#E0352B", press="#C0251B"
        ))
        delete_btn.clicked.connect(lambda: self.delete_clicked.emit(self.task_id))
        layout.addWidget(delete_btn)
