# MCP Settings Page - MCP 服务器设置页面
import sys
import asyncio
from pathlib import Path
src_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_path))

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QPushButton,
    QDialog, QFormLayout, QLineEdit, QComboBox,
    QTextEdit, QMessageBox, QCheckBox, QScrollArea
)
from PySide6.QtCore import Qt, QThread, Signal as QSignal

from .styles import ANIME_STYLE, COMBO_BOX_STYLE
from agent.mcp import MCPServer, get_mcp_config
from utils import get_logger

logger = get_logger()

# 统一样式
CARD_STYLE = """
    QListWidget {
        border: 1px solid #e8e8e8;
        border-radius: 8px;
        background-color: #fafafa;
        padding: 4px;
    }
    QListWidget::item {
        padding: 12px 8px;
        border-radius: 6px;
        margin: 2px 0;
    }
    QListWidget::item:hover {
        background-color: #f0f5ff;
    }
    QListWidget::item:selected {
        background-color: #e6f4ff;
        color: #1890ff;
    }
"""

FORM_INPUT_STYLE = """
    QLineEdit, QTextEdit, QComboBox {
        border: 1px solid #d9d9d9;
        border-radius: 6px;
        padding: 8px 12px;
        background: white;
        font-size: 13px;
    }
    QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
        border-color: #40a9ff;
        outline: none;
    }
    QLineEdit:disabled, QTextEdit:disabled {
        background-color: #f5f5f5;
        color: #999;
    }
"""

BTN_PRIMARY_STYLE = """
    QPushButton {
        background: #1890ff;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 8px 16px;
        font-size: 13px;
        font-weight: 500;
    }
    QPushButton:hover {
        background: #40a9ff;
    }
    QPushButton:pressed {
        background: #096dd9;
    }
"""

BTN_SECONDARY_STYLE = """
    QPushButton {
        background: white;
        color: #666;
        border: 1px solid #d9d9d9;
        border-radius: 6px;
        padding: 8px 16px;
        font-size: 13px;
    }
    QPushButton:hover {
        color: #1890ff;
        border-color: #1890ff;
    }
"""

BTN_DANGER_STYLE = """
    QPushButton {
        background: white;
        color: #ff4d4f;
        border: 1px solid #ffccc7;
        border-radius: 6px;
        padding: 8px 16px;
        font-size: 13px;
    }
    QPushButton:hover {
        background: #fff1f0;
        border-color: #ff4d4f;
    }
"""


class ToolLoadThread(QThread):
    """工具加载线程"""
    finished = QSignal(bool, list, str)

    def __init__(self, server: MCPServer):
        super().__init__()
        self.server = server

    def run(self):
        try:
            import asyncio
            from langchain_mcp_adapters.tools import load_mcp_tools

            async def load():
                if self.server.transport == "stdio":
                    connection = {
                        "transport": "stdio",
                        "command": self.server.command,
                        "args": self.server.args or []
                    }
                    if self.server.env:
                        connection["env"] = self.server.env
                elif self.server.transport == "streamable_http":
                    connection = {"transport": "streamable_http", "url": self.server.url}
                else:
                    connection = {"transport": "sse", "url": self.server.url}
                return await load_mcp_tools(session=None, connection=connection)

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                tools = loop.run_until_complete(load())
            finally:
                loop.close()

            tool_list = []
            for tool in tools:
                schema = {}
                if hasattr(tool, "args_schema") and tool.args_schema:
                    s = tool.args_schema
                    schema = s.model_json_schema() if hasattr(s, "model_json_schema") else (s if isinstance(s, dict) else {})
                tool_list.append({
                    "name": getattr(tool, "name", str(tool)),
                    "description": getattr(tool, "description", ""),
                    "inputSchema": schema
                })
            self.finished.emit(True, tool_list, "")
        except* Exception as eg:
            msgs = [str(e) for e in eg.exceptions]
            self.finished.emit(False, [], "; ".join(msgs))


class ToolTestThread(QThread):
    """工具测试线程"""
    finished = QSignal(bool, str, str)

    def __init__(self, server: MCPServer, tool_name: str, args: dict):
        super().__init__()
        self.server = server
        self.tool_name = tool_name
        self.args = args

    def run(self):
        try:
            import asyncio
            import json
            from langchain_mcp_adapters.tools import load_mcp_tools

            async def test():
                if self.server.transport == "stdio":
                    conn = {"transport": "stdio", "command": self.server.command, "args": self.server.args or []}
                    if self.server.env:
                        conn["env"] = self.server.env
                elif self.server.transport == "streamable_http":
                    conn = {"transport": "streamable_http", "url": self.server.url}
                else:
                    conn = {"transport": "sse", "url": self.server.url}
                
                tools = await load_mcp_tools(session=None, connection=conn)
                for t in tools:
                    if getattr(t, "name", "") == self.tool_name:
                        result = await t.ainvoke(self.args)
                        return True, json.dumps(result, ensure_ascii=False, indent=2) if isinstance(result, (dict, list)) else str(result), ""
                return False, "", f"工具 '{self.tool_name}' 未找到"

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                success, result, error = loop.run_until_complete(test())
            finally:
                loop.close()
            self.finished.emit(success, result, error)
        except* Exception as eg:
            self.finished.emit(False, "", "; ".join(str(e) for e in eg.exceptions))


class MCPTestDialog(QDialog):
    """MCP 工具测试对话框"""

    def __init__(self, parent=None, server: MCPServer = None):
        super().__init__(parent)
        self.server = server
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle(f"测试 - {self.server.name if self.server else ''}")
        self.setFixedSize(500, 450)
        self.setStyleSheet(ANIME_STYLE)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # 状态
        self.status_label = QLabel("正在连接...")
        self.status_label.setStyleSheet("color: #1890ff; font-size: 12px; padding: 8px;")
        layout.addWidget(self.status_label)

        # 工具列表
        self.tools_list = QListWidget()
        self.tools_list.setStyleSheet(CARD_STYLE)
        self.tools_list.itemClicked.connect(self._on_tool_selected)
        layout.addWidget(self.tools_list)

        # 工具描述
        self.tool_desc = QTextEdit()
        self.tool_desc.setReadOnly(True)
        self.tool_desc.setPlaceholderText("选择工具查看说明")
        self.tool_desc.setMaximumHeight(80)
        self.tool_desc.setStyleSheet(FORM_INPUT_STYLE)
        layout.addWidget(self.tool_desc)

        # 测试输入
        self.test_input = QTextEdit()
        self.test_input.setPlaceholderText('参数 (JSON): {"key": "value"}')
        self.test_input.setMaximumHeight(60)
        self.test_input.setStyleSheet(FORM_INPUT_STYLE)
        layout.addWidget(self.test_input)

        # 执行按钮
        test_btn = QPushButton("执行测试")
        test_btn.setStyleSheet(BTN_PRIMARY_STYLE)
        test_btn.clicked.connect(self._run_test)
        layout.addWidget(test_btn)

        # 结果
        self.test_result = QTextEdit()
        self.test_result.setReadOnly(True)
        self.test_result.setPlaceholderText("结果...")
        self.test_result.setMaximumHeight(100)
        self.test_result.setStyleSheet(FORM_INPUT_STYLE)
        layout.addWidget(self.test_result)

        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.setStyleSheet(BTN_SECONDARY_STYLE)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        self._load_tools()

    def _load_tools(self):
        self._load_thread = ToolLoadThread(self.server)
        self._load_thread.finished.connect(self._on_tools_loaded)
        self._load_thread.start()

    def _on_tools_loaded(self, success: bool, tools: list, error: str):
        if success and tools:
            self.status_label.setText(f"已连接，{len(tools)} 个工具")
            self.status_label.setStyleSheet("color: #52c41a; font-size: 12px; padding: 8px;")
            for tool in tools:
                item = QListWidgetItem(f"  {tool['name']}")
                item.setData(Qt.ItemDataRole.UserRole, tool)
                self.tools_list.addItem(item)
        else:
            self.status_label.setText(f"连接失败: {error}")
            self.status_label.setStyleSheet("color: #ff4d4f; font-size: 12px; padding: 8px;")

    def _on_tool_selected(self, item: QListWidgetItem):
        tool = item.data(Qt.ItemDataRole.UserRole)
        if tool:
            self.tool_desc.setText(f"{tool.get('name', '')}\n{tool.get('description', '')}")

    def _run_test(self):
        import json
        item = self.tools_list.currentItem()
        if not item:
            return
        tool = item.data(Qt.ItemDataRole.UserRole)
        args = {}
        text = self.test_input.toPlainText().strip()
        if text:
            try:
                args = json.loads(text)
            except:
                self.test_result.setText("JSON 格式错误")
                return
        self.test_result.setText("执行中...")
        self._test_thread = ToolTestThread(self.server, tool["name"], args)
        self._test_thread.finished.connect(lambda s, r, e: self.test_result.setText(r if s else f"错误: {e}"))
        self._test_thread.start()


class MCPServerDialog(QDialog):
    """添加/编辑 MCP 服务器"""

    def __init__(self, parent=None, server: MCPServer = None):
        self.server = server or MCPServer(id="", name="", transport="streamable_http", command="", args=[], env={}, enabled=True)
        self._is_edit = bool(server and server.id)
        super().__init__(parent)
        self._setup_ui()
        self._load_values()

    def _setup_ui(self):
        self.setWindowTitle("编辑服务器" if self._is_edit else "添加服务器")
        self.setMinimumSize(480, 400)
        self.setStyleSheet(ANIME_STYLE)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)

        # 表单
        form = QFormLayout()
        form.setSpacing(10)

        self.id_edit = QLineEdit()
        self.id_edit.setPlaceholderText("唯一标识，如: filesystem")
        self.id_edit.setStyleSheet(FORM_INPUT_STYLE)
        form.addRow("ID:", self.id_edit)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("显示名称")
        self.name_edit.setStyleSheet(FORM_INPUT_STYLE)
        form.addRow("名称:", self.name_edit)

        self.transport_combo = QComboBox()
        self.transport_combo.addItems(["streamable_http", "stdio", "sse"])
        self.transport_combo.setStyleSheet(COMBO_BOX_STYLE)
        self.transport_combo.currentTextChanged.connect(self._on_transport_changed)
        form.addRow("传输:", self.transport_combo)

        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("https://...")
        self.url_edit.setStyleSheet(FORM_INPUT_STYLE)
        form.addRow("URL:", self.url_edit)

        self.command_edit = QLineEdit()
        self.command_edit.setPlaceholderText("命令")
        self.command_edit.setStyleSheet(FORM_INPUT_STYLE)
        self.command_edit.setVisible(False)
        form.addRow("命令:", self.command_edit)

        self.args_edit = QLineEdit()
        self.args_edit.setPlaceholderText("参数")
        self.args_edit.setStyleSheet(FORM_INPUT_STYLE)
        self.args_edit.setVisible(False)
        form.addRow("参数:", self.args_edit)

        self.enabled_check = QCheckBox("启用")
        self.enabled_check.setChecked(True)
        form.addRow("", self.enabled_check)

        layout.addLayout(form)

        # 工具预览
        self.tools_preview = QTextEdit()
        self.tools_preview.setReadOnly(True)
        self.tools_preview.setPlaceholderText("点击「测试」查看可用工具")
        self.tools_preview.setMaximumHeight(80)
        self.tools_preview.setStyleSheet(FORM_INPUT_STYLE)
        layout.addWidget(self.tools_preview)

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        test_btn = QPushButton("测试连接")
        test_btn.setStyleSheet(BTN_SECONDARY_STYLE)
        test_btn.clicked.connect(self._test_connection)
        btn_layout.addWidget(test_btn)

        btn_layout.addStretch()

        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet(BTN_SECONDARY_STYLE)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("保存")
        save_btn.setStyleSheet(BTN_PRIMARY_STYLE)
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _on_transport_changed(self, transport: str):
        is_stdio = transport == "stdio"
        self.url_edit.setVisible(not is_stdio)
        self.command_edit.setVisible(is_stdio)
        self.args_edit.setVisible(is_stdio)

    def _load_values(self):
        if self.server.id:
            self.id_edit.setText(self.server.id)
            self.id_edit.setEnabled(False)
        self.name_edit.setText(self.server.name)
        self.transport_combo.setCurrentText(self.server.transport)
        self.url_edit.setText(self.server.url)
        self.command_edit.setText(self.server.command)
        self.args_edit.setText(" ".join(self.server.args or []))
        self.enabled_check.setChecked(self.server.enabled)
        self._on_transport_changed(self.server.transport)

    def _test_connection(self):
        server = self._build_temp_server()
        if server:
            self.tools_preview.setText("连接中...")
            self._test_thread = ToolLoadThread(server)
            self._test_thread.finished.connect(self._on_test_result)
            self._test_thread.start()

    def _on_test_result(self, success: bool, tools: list, error: str):
        if success and tools:
            self.tools_preview.setText(f"✓ 发现 {len(tools)} 个工具:\n" + "\n".join(f"  • {t['name']}" for t in tools[:10]))
        else:
            self.tools_preview.setText(f"✗ {error}")

    def _build_temp_server(self) -> MCPServer:
        import json
        transport = self.transport_combo.currentText()
        env = {}
        env_text = self.env_edit.toPlainText().strip() if hasattr(self, 'env_edit') else ""
        if env_text:
            try:
                env = json.loads(env_text)
            except:
                pass
        return MCPServer(
            id=self.id_edit.text().strip() or "test",
            name=self.name_edit.text().strip() or "测试",
            transport=transport,
            command=self.command_edit.text().strip(),
            args=self.args_edit.text().split() if self.args_edit.text() else [],
            url=self.url_edit.text().strip(),
            env=env,
            enabled=True
        )

    def _save(self):
        import json

        server_id = self.id_edit.text().strip()
        if not server_id:
            QMessageBox.warning(self, "提示", "请输入 ID")
            return

        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "提示", "请输入名称")
            return

        transport = self.transport_combo.currentText()
        if transport == "stdio" and not self.command_edit.text().strip():
            QMessageBox.warning(self, "提示", "请输入命令")
            return

        if transport != "stdio" and not self.url_edit.text().strip():
            QMessageBox.warning(self, "提示", "请输入 URL")
            return

        self.server.id = server_id
        self.server.name = name
        self.server.transport = transport
        self.server.command = self.command_edit.text().strip()
        self.server.args = self.args_edit.text().split() if self.args_edit.text() else []
        self.server.url = self.url_edit.text().strip()
        self.server.enabled = self.enabled_check.isChecked()

        self.accept()

    def get_server(self) -> MCPServer:
        return self.server


class MCPSettingsPage(QWidget):
    """MCP 服务器设置页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = get_mcp_config()
        self._setup_ui()
        self._load_servers()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(content)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # 标题区
        header = QLabel("MCP 服务器")
        header.setStyleSheet("font-size: 18px; font-weight: 600; color: #262626;")
        layout.addWidget(header)

        desc = QLabel("管理外部工具服务器连接")
        desc.setStyleSheet("font-size: 12px; color: #8c8c8c;")
        layout.addWidget(desc)

        # 服务器列表
        self.server_list = QListWidget()
        self.server_list.setStyleSheet(CARD_STYLE)
        self.server_list.setMinimumHeight(200)
        self.server_list.itemDoubleClicked.connect(self._edit_selected)
        layout.addWidget(self.server_list)

        # 操作按钮
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        add_btn = QPushButton("添加服务器")
        add_btn.setStyleSheet(BTN_PRIMARY_STYLE)
        add_btn.clicked.connect(self._add_server)
        btn_layout.addWidget(add_btn)

        edit_btn = QPushButton("编辑")
        edit_btn.setStyleSheet(BTN_SECONDARY_STYLE)
        edit_btn.clicked.connect(self._edit_selected)
        btn_layout.addWidget(edit_btn)

        delete_btn = QPushButton("删除")
        delete_btn.setStyleSheet(BTN_DANGER_STYLE)
        delete_btn.clicked.connect(self._delete_selected)
        btn_layout.addWidget(delete_btn)

        test_btn = QPushButton("测试")
        test_btn.setStyleSheet(BTN_SECONDARY_STYLE)
        test_btn.clicked.connect(self._test_selected)
        btn_layout.addWidget(test_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        layout.addStretch()
        scroll.setWidget(content)
        main_layout.addWidget(scroll)

    def _load_servers(self):
        self.server_list.clear()
        for server in self.config.servers:
            icon = "✓" if server.enabled else "○"
            transport = server.transport.replace("_", " ")
            item = QListWidgetItem(f"  {icon} {server.name}  ·  {transport}")
            item.setData(Qt.ItemDataRole.UserRole, server.id)
            self.server_list.addItem(item)

    def _add_server(self):
        dialog = MCPServerDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                self.config.add_server(dialog.get_server())
                self._load_servers()
            except ValueError as e:
                QMessageBox.warning(self, "错误", str(e))

    def _edit_selected(self):
        item = self.server_list.currentItem()
        if not item:
            return
        server = self.config.get_server(item.data(Qt.ItemDataRole.UserRole))
        if server:
            dialog = MCPServerDialog(self, server)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.config.update_server(server.id, dialog.get_server())
                self._load_servers()

    def _delete_selected(self):
        item = self.server_list.currentItem()
        if not item:
            return
        server = self.config.get_server(item.data(Qt.ItemDataRole.UserRole))
        if server and QMessageBox.question(self, "确认", f"删除「{server.name}」?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.config.remove_server(server.id)
            self._load_servers()

    def _test_selected(self):
        item = self.server_list.currentItem()
        if not item:
            return
        server = self.config.get_server(item.data(Qt.ItemDataRole.UserRole))
        if server:
            MCPTestDialog(self, server).exec()

    def save(self):
        pass

    def reset(self):
        self._load_servers()
