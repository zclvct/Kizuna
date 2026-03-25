# Cron Expression Builder
import sys
from pathlib import Path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QSpinBox, QCheckBox,
    QGroupBox, QButtonGroup, QRadioButton, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont


class CronBuilderDialog(QDialog):
    """Cron 表达式构建器"""

    cron_built = Signal(str)

    def __init__(self, initial_cron: str = "", parent=None):
        super().__init__(parent)
        self.initial_cron = initial_cron
        self.current_mode = "custom"
        self._setup_ui()
        self._parse_initial_cron()

    def _setup_ui(self):
        """设置 UI"""
        self.setWindowTitle("Cron 表达式构建器")
        self.setMinimumSize(550, 500)
        # 设置窗口标志 - 不在任务栏显示
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.MSWindowsFixedSizeDialogHint | Qt.WindowType.Tool)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # 标题
        title = QLabel("🕐 Cron 表达式构建器")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(title)

        # 模式选择
        mode_group = QGroupBox("选择模式")
        mode_layout = QVBoxLayout()

        self.mode_buttons = QButtonGroup()
        self.mode_daily = QRadioButton("每天 (固定时间)")
        self.mode_weekly = QRadioButton("每周 (固定星期)")
        self.mode_monthly = QRadioButton("每月 (固定日期)")
        self.mode_hourly = QRadioButton("每小时")
        self.mode_custom = QRadioButton("自定义")

        self.mode_daily.setChecked(True)
        self.mode_buttons.addButton(self.mode_daily, 0)
        self.mode_buttons.addButton(self.mode_weekly, 1)
        self.mode_buttons.addButton(self.mode_monthly, 2)
        self.mode_buttons.addButton(self.mode_hourly, 3)
        self.mode_buttons.addButton(self.mode_custom, 4)

        self.mode_buttons.buttonClicked.connect(self._on_mode_changed)

        mode_layout.addWidget(self.mode_daily)
        mode_layout.addWidget(self.mode_weekly)
        mode_layout.addWidget(self.mode_monthly)
        mode_layout.addWidget(self.mode_hourly)
        mode_layout.addWidget(self.mode_custom)
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)

        # 时间配置
        self.time_group = QGroupBox("时间配置")
        time_layout = QVBoxLayout()

        # 小时和分钟
        hour_min_layout = QHBoxLayout()

        hour_layout = QVBoxLayout()
        hour_layout.addWidget(QLabel("小时 (0-23):"))
        self.hour_spin = QSpinBox()
        self.hour_spin.setRange(0, 23)
        self.hour_spin.setValue(8)
        hour_layout.addWidget(self.hour_spin)
        hour_min_layout.addLayout(hour_layout)

        min_layout = QVBoxLayout()
        min_layout.addWidget(QLabel("分钟 (0-59):"))
        self.minute_spin = QSpinBox()
        self.minute_spin.setRange(0, 59)
        self.minute_spin.setValue(0)
        min_layout.addWidget(self.minute_spin)
        hour_min_layout.addLayout(min_layout)

        time_layout.addLayout(hour_min_layout)

        # 星期选择 (仅每周模式显示)
        self.weekday_group = QGroupBox("选择星期")
        weekday_layout = QHBoxLayout()
        weekdays = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"]
        self.weekday_checkboxes = []
        for i, day in enumerate(weekdays):
            cb = QCheckBox(day)
            self.weekday_checkboxes.append(cb)
            weekday_layout.addWidget(cb)
        self.weekday_group.setLayout(weekday_layout)
        self.weekday_group.setVisible(False)
        time_layout.addWidget(self.weekday_group)

        # 日期选择 (仅每月模式显示)
        self.day_group = QGroupBox("选择日期")
        day_layout = QHBoxLayout()
        day_label = QLabel("每月第")
        self.day_spin = QSpinBox()
        self.day_spin.setRange(1, 31)
        self.day_spin.setValue(1)
        day_label2 = QLabel("天:")
        day_layout.addWidget(day_label)
        day_layout.addWidget(self.day_spin)
        day_layout.addWidget(day_label2)
        day_layout.addStretch()
        self.day_group.setLayout(day_layout)
        self.day_group.setVisible(False)
        time_layout.addWidget(self.day_group)

        self.time_group.setLayout(time_layout)
        layout.addWidget(self.time_group)

        # 自定义编辑 (仅自定义模式显示)
        self.custom_group = QGroupBox("自定义 Cron 表达式")
        custom_layout = QVBoxLayout()

        self.cron_parts = []
        part_labels = ["分 (0-59)", "时 (0-23)", "日 (1-31)", "月 (1-12)", "周 (0-6)"]
        part_defaults = ["0", "8", "*", "*", "*"]

        for label, default in zip(part_labels, part_defaults):
            part_layout = QHBoxLayout()
            part_layout.addWidget(QLabel(label))
            part_edit = QSpinBox() if label != "日 (1-31)" and label != "月 (1-12)" else QSpinBox()

            from PySide6.QtWidgets import QLineEdit
            part_edit = QLineEdit()
            part_edit.setText(default)
            part_edit.setPlaceholderText("*")
            self.cron_parts.append(part_edit)
            part_layout.addWidget(part_edit)
            custom_layout.addLayout(part_layout)

        self.custom_group.setLayout(custom_layout)
        self.custom_group.setVisible(False)
        layout.addWidget(self.custom_group)

        # 预览
        preview_group = QGroupBox("预览")
        preview_layout = QVBoxLayout()
        self.preview_label = QLabel()
        self.preview_label.setFont(QFont("Monospace", 12))
        self.preview_label.setStyleSheet("color: #007AFF; padding: 10px; background-color: #F0F8FF; border-radius: 6px;")
        preview_layout.addWidget(self.preview_label)
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)

        # 按钮区
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        apply_btn = QPushButton("应用")
        apply_btn.clicked.connect(self._apply_cron)
        btn_layout.addWidget(apply_btn)

        layout.addLayout(btn_layout)

        # 连接信号
        self.hour_spin.valueChanged.connect(self._update_preview)
        self.minute_spin.valueChanged.connect(self._update_preview)
        self.day_spin.valueChanged.connect(self._update_preview)
        for cb in self.weekday_checkboxes:
            cb.stateChanged.connect(self._update_preview)
        for edit in self.cron_parts:
            edit.textChanged.connect(self._update_preview)

        # 初始预览
        self._update_preview()

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
            QSpinBox, QLineEdit {
                padding: 6px;
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                background-color: white;
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

    def _on_mode_changed(self, button):
        """模式切换"""
        mode_id = self.mode_buttons.id(button)

        self.time_group.setVisible(mode_id in [0, 1, 2])  # 每天、每周、每月
        self.weekday_group.setVisible(mode_id == 1)  # 仅每周
        self.day_group.setVisible(mode_id == 2)  # 仅每月
        self.custom_group.setVisible(mode_id == 4)  # 仅自定义

        self._update_preview()

    def _parse_initial_cron(self):
        """解析初始 Cron 表达式"""
        if not self.initial_cron:
            return

        parts = self.initial_cron.split()
        if len(parts) != 5:
            return

        minute, hour, day, month, dow = parts

        # 检查是否匹配预定义模式
        if day == "*" and month == "*" and dow == "*":
            # 可能是每天或每小时
            if hour == "*":
                self.mode_hourly.setChecked(True)
            else:
                self.mode_daily.setChecked(True)
                try:
                    self.hour_spin.setValue(int(hour))
                    self.minute_spin.setValue(int(minute))
                except:
                    pass
        elif day == "*" and month == "*" and dow != "*":
            # 每周
            self.mode_weekly.setChecked(True)
            try:
                self.hour_spin.setValue(int(hour))
                self.minute_spin.setValue(int(minute))
                if "," in dow:
                    for i in dow.split(","):
                        idx = int(i)
                        if idx < len(self.weekday_checkboxes):
                            self.weekday_checkboxes[idx].setChecked(True)
                else:
                    idx = int(dow)
                    if idx < len(self.weekday_checkboxes):
                        self.weekday_checkboxes[idx].setChecked(True)
            except:
                pass
        elif day != "*" and month == "*" and dow == "*":
            # 每月
            self.mode_monthly.setChecked(True)
            try:
                self.hour_spin.setValue(int(hour))
                self.minute_spin.setValue(int(minute))
                self.day_spin.setValue(int(day))
            except:
                pass
        else:
            # 自定义
            self.mode_custom.setChecked(True)
            for i, part in enumerate(parts):
                if i < len(self.cron_parts):
                    self.cron_parts[i].setText(part)

    def _update_preview(self):
        """更新预览"""
        mode_id = self.mode_buttons.checkedId()

        if mode_id == 0:  # 每天
            cron = f"{self.minute_spin.value()} {self.hour_spin.value()} * * *"
            desc = f"每天 {self.hour_spin.value():02d}:{self.minute_spin.value():02d}"
        elif mode_id == 1:  # 每周
            hour = self.hour_spin.value()
            minute = self.minute_spin.value()
            selected_days = [str(i) for i, cb in enumerate(self.weekday_checkboxes) if cb.isChecked()]
            if selected_days:
                dow = ",".join(selected_days)
                cron = f"{minute} {hour} * * {dow}"
                day_names = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"]
                days_text = ", ".join([day_names[int(i)] for i in selected_days])
                desc = f"每 {days_text} {hour:02d}:{minute:02d}"
            else:
                cron = f"{minute} {hour} * * *"
                desc = f"每天 {hour:02d}:{minute:02d} (未选择星期)"
        elif mode_id == 2:  # 每月
            day = self.day_spin.value()
            hour = self.hour_spin.value()
            minute = self.minute_spin.value()
            cron = f"{minute} {hour} {day} * *"
            desc = f"每月 {day} 号 {hour:02d}:{minute:02d}"
        elif mode_id == 3:  # 每小时
            cron = "0 * * * *"
            desc = "每小时"
        else:  # 自定义
            parts = [edit.text() or "*" for edit in self.cron_parts]
            cron = " ".join(parts)
            desc = "自定义"

        self.preview_label.setText(f"{cron}\n{desc}")

    def _apply_cron(self):
        """应用 Cron 表达式"""
        self._update_preview()
        cron = self.preview_label.text().split("\n")[0]

        # 验证
        parts = cron.split()
        if len(parts) != 5:
            QMessageBox.warning(self, "验证失败", "Cron 表达式格式不正确")
            return

        self.cron_built.emit(cron)
        self.accept()
