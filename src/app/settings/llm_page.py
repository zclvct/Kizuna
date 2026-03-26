# LLM Settings Page
import sys
from pathlib import Path
src_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_path))

from functools import partial

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QGridLayout, QScrollArea, QDialog,
    QFormLayout, QLineEdit, QComboBox, QPushButton,
    QMessageBox, QMenu, QDoubleSpinBox, QSpinBox, QSlider
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter, QColor, QPen, QBrush

from .styles import ANIME_STYLE, COMBO_BOX_STYLE, CARD_STYLE, MENU_STYLE
from utils import get_config, get_logger

logger = get_logger()


class LLMProviderCard(QFrame):
    """LLM 服务商卡片"""
    
    clicked = Signal()
    edit_requested = Signal()  # 请求编辑
    delete_requested = Signal()
    
    def __init__(self, provider_data: dict, is_default: bool = False, is_add_card: bool = False):
        super().__init__()
        self.provider_data = provider_data
        self.is_default = is_default
        self.is_add_card = is_add_card
        self._setup_ui()
        
    def _setup_ui(self):
        self.setFixedSize(140, 100)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        if self.is_add_card:
            self.setObjectName("addCard")
            self.setStyleSheet(CARD_STYLE)
            add_label = QLabel("➕")
            add_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            add_label.setStyleSheet("font-size: 32px; background: transparent;")
            layout.addWidget(add_label)
            
            hint_label = QLabel("添加服务商")
            hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            hint_label.setStyleSheet("color: #999; font-size: 11px; background: transparent;")
            layout.addWidget(hint_label)
        else:
            self.setObjectName("cardDefault" if self.is_default else "card")
            self.setStyleSheet(CARD_STYLE)
            
            # 图标
            icon_label = QLabel(self._get_icon())
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_label.setStyleSheet("font-size: 28px; background: transparent;")
            layout.addWidget(icon_label)
            
            # 名称
            name = self.provider_data.get('name', 'Unknown')
            name_label = QLabel(name)
            name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            name_label.setStyleSheet("color: #333; font-size: 12px; font-weight: bold; background: transparent;")
            layout.addWidget(name_label)
            
            # 模型
            model = self.provider_data.get('model', '')
            if model:
                model_label = QLabel(model[:15] + ('...' if len(model) > 15 else ''))
                model_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                model_label.setStyleSheet("color: #999; font-size: 10px; background: transparent;")
                layout.addWidget(model_label)
    
    def _get_icon(self) -> str:
        """获取服务商图标"""
        provider_type = self.provider_data.get('provider', '').lower()
        icons = {
            'openai': '🤖',
            'anthropic': '🧠',
            'ollama': '🦙',
            'azure': '☁️',
            'google': '🌟',
            'deepseek': '🔮',
            'moonshot': '🌙',
            'zhipu': '💎',
        }
        return icons.get(provider_type, '🔌')
    
    def set_default(self, is_default: bool):
        """设置是否为默认"""
        self.is_default = is_default
        self.setObjectName("cardDefault" if is_default else "card")
        self.setStyleSheet(CARD_STYLE)
        self.update()
    
    def paintEvent(self, event):
        super().paintEvent(event)
        if self.is_default and not self.is_add_card:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # 绘制圆形背景
            painter.setBrush(QBrush(QColor("#5c9eff")))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(self.width() - 28, self.height() - 28, 22, 22)
            
            # 绘制对号
            painter.setPen(QPen(QColor("white"), 2.5))
            painter.drawLine(self.width() - 22, self.height() - 17, self.width() - 18, self.height() - 13)
            painter.drawLine(self.width() - 18, self.height() - 13, self.width() - 12, self.height() - 22)
    
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
            edit_action = menu.addAction("✏️ 编辑")
            menu.addSeparator()
            delete_action = menu.addAction("🗑️ 删除")
            
            action = menu.exec(event.globalPos())
            
            if action == set_default_action:
                self.clicked.emit()
            elif action == edit_action:
                self.edit_requested.emit()
            elif action == delete_action:
                self.delete_requested.emit()


class LLMProviderDialog(QDialog):
    """添加/编辑 LLM 服务商对话框"""
    
    def __init__(self, parent=None, provider_data: dict = None):
        self.provider_data = provider_data or {
            'name': '',
            'provider': 'openai',
            'model': '',
            'api_key': '',
            'base_url': '',
            'temperature': 0.7,
            'max_tokens': 2000
        }
        super().__init__(parent)
        self._setup_ui()
        self._load_values()
    
    def _setup_ui(self):
        self.setWindowTitle("添加服务商" if not self.provider_data.get('name') else "编辑服务商")
        self.setMinimumSize(450, 520)
        self.setStyleSheet(ANIME_STYLE)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(12)
        
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
        layout.setSpacing(12)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 表单
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        # 显示名称
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("例如: 我的GPT-4")
        form_layout.addRow("显示名称:", self.name_edit)
        
        # 提供商类型
        self.provider_combo = QComboBox()
        self.provider_combo.addItems([
            "openai", "anthropic", "ollama", "azure", 
            "google", "deepseek", "moonshot", "zhipu", "custom"
        ])
        self.provider_combo.setStyleSheet(COMBO_BOX_STYLE)
        self.provider_combo.currentTextChanged.connect(self._on_provider_changed)
        form_layout.addRow("提供商类型:", self.provider_combo)
        
        # 模型
        self.model_edit = QLineEdit()
        self.model_edit.setPlaceholderText("例如: gpt-4 / claude-3-opus")
        form_layout.addRow("模型:", self.model_edit)
        
        # API Key
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_edit.setPlaceholderText("sk-...")
        form_layout.addRow("API Key:", self.api_key_edit)
        
        # Base URL
        self.base_url_edit = QLineEdit()
        self.base_url_edit.setPlaceholderText("可选，自定义API地址")
        form_layout.addRow("Base URL:", self.base_url_edit)
        
        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background: #e0e0e0;")
        form_layout.addRow(separator)
        
        # Temperature - 使用滑块+数值输入
        temp_layout = QHBoxLayout()
        self.temp_slider = QSlider(Qt.Orientation.Horizontal)
        self.temp_slider.setRange(0, 200)
        self.temp_slider.setValue(70)
        self.temp_slider.setMaximumWidth(150)
        self.temp_slider.valueChanged.connect(self._on_temp_slider_changed)
        
        self.temp_spin = QDoubleSpinBox()
        self.temp_spin.setRange(0.0, 2.0)
        self.temp_spin.setSingleStep(0.1)
        self.temp_spin.setValue(0.7)
        self.temp_spin.setMaximumWidth(80)
        self.temp_spin.valueChanged.connect(self._on_temp_spin_changed)
        
        temp_layout.addWidget(self.temp_slider)
        temp_layout.addWidget(self.temp_spin)
        temp_layout.addStretch()
        form_layout.addRow("Temperature:", temp_layout)
        
        # Max Tokens - 使用滑块+数值输入（以 token 为单位）
        tokens_layout = QHBoxLayout()
        self.tokens_slider = QSlider(Qt.Orientation.Horizontal)
        self.tokens_slider.setRange(100, 32000)  # 100 - 32000 tokens
        self.tokens_slider.setValue(2000)  # 默认 2000
        self.tokens_slider.setSingleStep(500)
        self.tokens_slider.setMaximumWidth(150)
        self.tokens_slider.valueChanged.connect(self._on_tokens_slider_changed)
        
        self.tokens_spin = QSpinBox()
        self.tokens_spin.setRange(100, 65536)
        self.tokens_spin.setSingleStep(500)
        self.tokens_spin.setValue(2000)
        self.tokens_spin.setMaximumWidth(100)
        self.tokens_spin.valueChanged.connect(self._on_tokens_spin_changed)
        
        tokens_layout.addWidget(self.tokens_slider)
        tokens_layout.addWidget(self.tokens_spin)
        tokens_layout.addStretch()
        form_layout.addRow("Max Tokens:", tokens_layout)
        
        layout.addLayout(form_layout)
        
        # 参数说明
        hint_label = QLabel("💡 Temperature 越高越随机，Max Tokens 限制最大输出 token 数量")
        hint_label.setStyleSheet("color: #888; font-size: 10px;")
        layout.addWidget(hint_label)
        
        layout.addStretch()
        
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)
        
        # 按钮 - 放在滚动区域外面
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("取消")
        cancel_btn.setObjectName("secondaryBtn")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)
        
        main_layout.addLayout(btn_layout)
    
    def _on_provider_changed(self, provider: str):
        """提供商类型变更时更新默认 Base URL"""
        default_urls = {
            'openai': '',
            'anthropic': 'https://api.anthropic.com/v1',
            'ollama': 'http://localhost:11434',
            'deepseek': 'https://api.deepseek.com/v1',
            'moonshot': 'https://api.moonshot.cn/v1',
            'zhipu': 'https://open.bigmodel.cn/api/paas/v4',
        }
        if provider in default_urls and not self.base_url_edit.text().strip():
            self.base_url_edit.setPlaceholderText(f"默认: {default_urls[provider]}" if default_urls[provider] else "可选")
    
    def _on_temp_slider_changed(self, value: int):
        """温度滑块变更"""
        self.temp_spin.blockSignals(True)
        self.temp_spin.setValue(value / 100.0)
        self.temp_spin.blockSignals(False)
    
    def _on_temp_spin_changed(self, value: float):
        """温度数值变更"""
        self.temp_slider.blockSignals(True)
        self.temp_slider.setValue(int(value * 100))
        self.temp_slider.blockSignals(False)
    
    def _on_tokens_slider_changed(self, value: int):
        """Max Tokens 滑块变更"""
        self.tokens_spin.blockSignals(True)
        self.tokens_spin.setValue(value)
        self.tokens_spin.blockSignals(False)
    
    def _on_tokens_spin_changed(self, value: int):
        """Max Tokens 数值变更"""
        self.tokens_slider.blockSignals(True)
        # 滑块最大 32000，SpinBox 可输入到 65536
        self.tokens_slider.setValue(min(value, self.tokens_slider.maximum()))
        self.tokens_slider.blockSignals(False)
    
    def _load_values(self):
        """加载值"""
        self.name_edit.setText(self.provider_data.get('name', ''))
        self.provider_combo.setCurrentText(self.provider_data.get('provider', 'openai'))
        self.model_edit.setText(self.provider_data.get('model', ''))
        self.api_key_edit.setText(self.provider_data.get('api_key', ''))
        self.base_url_edit.setText(self.provider_data.get('base_url', ''))
        
        # 加载温度
        temperature = self.provider_data.get('temperature', 0.7)
        self.temp_spin.setValue(temperature)
        self.temp_slider.setValue(int(temperature * 100))
        
        # 加载 max_tokens（直接使用 token 数值）
        max_tokens = self.provider_data.get('max_tokens', 2000)
        max_tokens = max(100, min(65536, max_tokens))
        self.tokens_spin.setValue(max_tokens)
        self.tokens_slider.setValue(min(max_tokens, self.tokens_slider.maximum()))
    
    def _save(self):
        """保存"""
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "提示", "请输入显示名称")
            return
        
        model = self.model_edit.text().strip()
        if not model:
            QMessageBox.warning(self, "提示", "请输入模型名称")
            return
        
        self.provider_data['name'] = name
        self.provider_data['provider'] = self.provider_combo.currentText()
        self.provider_data['model'] = model
        self.provider_data['api_key'] = self.api_key_edit.text().strip()
        self.provider_data['base_url'] = self.base_url_edit.text().strip()
        self.provider_data['temperature'] = self.temp_spin.value()
        self.provider_data['max_tokens'] = self.tokens_spin.value()
        
        self.accept()
    
    def get_data(self) -> dict:
        """获取数据"""
        return self.provider_data


class LLMSettingsPage(QWidget):
    """LLM 设置页面"""
    
    config_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = get_config()
        self._providers = []
        self._default_provider_index = 0
        self._setup_ui()
        self._load_config()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 标题
        title = QLabel("🤖 LLM 服务商配置")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        layout.addWidget(title)
        
        # 提示
        hint = QLabel("点击卡片设为默认，右键可编辑或删除")
        hint.setStyleSheet("color: #999; font-size: 11px;")
        layout.addWidget(hint)
        
        # 服务商卡片区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        self.providers_layout = QGridLayout(scroll_content)
        self.providers_layout.setSpacing(15)
        self.providers_layout.setContentsMargins(5, 5, 5, 5)
        self.providers_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        # MCP 工具状态区域（简化版）
        mcp_frame = QFrame()
        mcp_frame.setStyleSheet("""
            QFrame {
                background: #f8f9fa;
                border: 1px solid #e8e8e8;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        mcp_layout = QHBoxLayout(mcp_frame)
        mcp_layout.setContentsMargins(12, 8, 12, 8)
        
        self.mcp_status_label = QLabel("MCP 工具: 检查中...")
        self.mcp_status_label.setStyleSheet("color: #666; font-size: 12px;")
        mcp_layout.addWidget(self.mcp_status_label)
        
        mcp_layout.addStretch()
        layout.addWidget(mcp_frame)
    
    def _load_config(self):
        """加载配置"""
        providers_config = getattr(self.config, 'llm_providers', None)
        
        if providers_config and providers_config.get('providers'):
            self._providers = providers_config.get('providers', [])
            self._default_provider_index = providers_config.get('default_index', 0)
        else:
            # 兼容旧配置格式
            self._providers = [{
                'name': self.config.llm.provider.upper(),
                'provider': self.config.llm.provider,
                'model': self.config.llm.model or '',
                'api_key': self.config.llm.api_key or '',
                'base_url': self.config.llm.base_url or '',
                'temperature': getattr(self.config.llm, 'temperature', 0.7) or 0.7,
                'max_tokens': getattr(self.config.llm, 'max_tokens', 2000) or 2000,
            }]
            self._default_provider_index = 0
        
        self._create_provider_cards()
        self._refresh_mcp_status()
    
    def _create_provider_cards(self):
        """创建服务商卡片"""
        # 清除现有卡片
        while self.providers_layout.count():
            item = self.providers_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # 添加卡片
        add_card = LLMProviderCard({}, is_add_card=True)
        add_card.clicked.connect(self._add_provider)
        self.providers_layout.addWidget(add_card, 0, 0)
        
        # 服务商卡片 - 使用 partial 避免闭包问题
        for i, provider in enumerate(self._providers):
            is_default = (i == self._default_provider_index)
            card = LLMProviderCard(provider, is_default=is_default)
            # 使用 partial 确保索引正确传递
            card.clicked.connect(partial(self._set_default_provider, i))
            card.edit_requested.connect(partial(self._edit_provider, i))
            card.delete_requested.connect(partial(self._delete_provider, i))
            row = (i + 1) // 4
            col = (i + 1) % 4
            self.providers_layout.addWidget(card, row, col)
    
    def _add_provider(self):
        """添加服务商"""
        dialog = LLMProviderDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._providers.append(dialog.get_data())
            self._create_provider_cards()
            self.config_changed.emit()
    
    def _edit_provider(self, index: int):
        """编辑服务商"""
        if 0 <= index < len(self._providers):
            dialog = LLMProviderDialog(self, self._providers[index].copy())
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self._providers[index] = dialog.get_data()
                self._create_provider_cards()
                self.config_changed.emit()
    
    def _set_default_provider(self, index: int):
        """设置默认服务商"""
        self._default_provider_index = index
        self._create_provider_cards()
        self.config_changed.emit()
    
    def _delete_provider(self, index: int):
        """删除服务商"""
        if len(self._providers) <= 1:
            QMessageBox.warning(self, "提示", "至少需要保留一个服务商")
            return
        
        reply = QMessageBox.question(
            self, "确认删除", 
            f"确定要删除 \"{self._providers[index].get('name', '')}\" 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            del self._providers[index]
            if self._default_provider_index >= len(self._providers):
                self._default_provider_index = len(self._providers) - 1
            self._create_provider_cards()
            self.config_changed.emit()
    
    def save(self):
        """保存配置"""
        # 保存多服务商配置
        self.config.llm_providers = {
            'providers': self._providers,
            'default_index': self._default_provider_index
        }
        
        # 更新当前激活的服务商
        if self._providers and 0 <= self._default_provider_index < len(self._providers):
            default_provider = self._providers[self._default_provider_index]
            self.config.llm.provider = default_provider.get('provider', 'openai')
            self.config.llm.model = default_provider.get('model', '')
            self.config.llm.api_key = default_provider.get('api_key', '') or None
            self.config.llm.base_url = default_provider.get('base_url', '') or None
            # 保存 temperature 和 max_tokens 到主配置
            self.config.llm.temperature = default_provider.get('temperature', 0.7)
            self.config.llm.max_tokens = default_provider.get('max_tokens', 2000)
        
        logger.info("LLM 配置已保存")
    
    def _refresh_mcp_status(self):
        """刷新 MCP 工具状态"""
        try:
            from agent.mcp import get_mcp_config, get_mcp_manager
            
            mcp_config = get_mcp_config()
            enabled_servers = mcp_config.get_enabled_servers()
            
            if not enabled_servers:
                self.mcp_status_label.setText("MCP: 未配置服务器")
                self.mcp_status_label.setStyleSheet("color: #faad14; font-size: 12px;")
            else:
                manager = get_mcp_manager()
                if manager.is_available():
                    self.mcp_status_label.setText(f"MCP: 加载中...")
                    self.mcp_status_label.setStyleSheet("color: #1890ff; font-size: 12px;")
                    self._load_mcp_tools_async()
                else:
                    self.mcp_status_label.setText("MCP: 需安装 langchain-mcp-adapters")
                    self.mcp_status_label.setStyleSheet("color: #ff4d4f; font-size: 12px;")
                    
        except Exception as e:
            self.mcp_status_label.setText(f"MCP: 错误 - {str(e)[:30]}")
            self.mcp_status_label.setStyleSheet("color: #ff4d4f; font-size: 12px;")
    
    def _load_mcp_tools_async(self):
        """异步加载 MCP 工具"""
        import asyncio
        from PySide6.QtCore import QThread, Signal as QSignal
        
        class LoadThread(QThread):
            finished = QSignal(list, str)
            
            def run(self):
                try:
                    from agent.tools.registry import get_tool_registry
                    registry = get_tool_registry()
                    
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        tools = loop.run_until_complete(registry.get_mcp_tools(force_reload=True))
                    finally:
                        loop.close()
                    
                    self.finished.emit([t.name for t in tools], "")
                except* Exception as eg:
                    self.finished.emit([], "; ".join(str(e) for e in eg.exceptions))
        
        def on_loaded(tool_names: list, error: str):
            if error:
                self.mcp_status_label.setText(f"MCP: 加载失败")
                self.mcp_status_label.setStyleSheet("color: #ff4d4f; font-size: 12px;")
            elif tool_names:
                self.mcp_status_label.setText(f"MCP: {len(tool_names)} 个工具已加载")
                self.mcp_status_label.setStyleSheet("color: #52c41a; font-size: 12px;")
            else:
                self.mcp_status_label.setText("MCP: 未发现工具")
                self.mcp_status_label.setStyleSheet("color: #faad14; font-size: 12px;")
        
        self._load_thread = LoadThread()
        self._load_thread.finished.connect(on_loaded)
        self._load_thread.start()
