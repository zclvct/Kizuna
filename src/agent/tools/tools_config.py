# Tools Configuration - 工具配置管理
from typing import List, Optional
from pathlib import Path
from pydantic import BaseModel
import json

from utils import get_logger

logger = get_logger()


class ToolItem(BaseModel):
    """工具项"""
    id: str
    name: str
    description: str = ""
    enabled: bool = True


class ToolsConfig:
    """工具配置管理"""
    
    def __init__(self):
        self._config_file = Path(__file__).parent.parent.parent.parent / "data" / "tools.json"
        self.tools: List[ToolItem] = []
        self._load()
    
    def _load(self):
        """加载配置"""
        if self._config_file.exists():
            try:
                with open(self._config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # 兼容旧格式 "skills" 键
                tools_data = data.get("skills", data.get("tools", []))
                self.tools = [ToolItem(**t) for t in tools_data]
                logger.info(f"已加载 {len(self.tools)} 个工具配置")
            except Exception as e:
                logger.error(f"加载工具配置失败: {e}")
                self._init_default_tools()
        else:
            self._init_default_tools()
    
    def _init_default_tools(self):
        """初始化默认工具"""
        self.tools = [
            ToolItem(id="time", name="时间工具", description="查询时间、日期、星期", enabled=True),
            ToolItem(id="weather", name="天气工具", description="查询天气预报", enabled=True),
            ToolItem(id="todo", name="待办事项", description="管理待办任务", enabled=True),
            ToolItem(id="clipboard", name="剪贴板助手", description="操作剪贴板内容", enabled=True),
            ToolItem(id="system", name="系统信息", description="查看电脑状态", enabled=True),
            ToolItem(id="launcher", name="应用启动", description="打开应用和文件", enabled=True),
            ToolItem(id="scheduler", name="定时任务", description="创建定时提醒", enabled=True),
            ToolItem(id="persona_edit", name="角色设定编辑", description="学习和修改设定", enabled=True),
            ToolItem(id="motion_control", name="动作控制", description="控制 Live2D 动作和表情", enabled=True),
            ToolItem(id="mood_emoji", name="心情表情", description="显示心情表情包", enabled=True),
            ToolItem(id="memory", name="记忆管理", description="自动记忆和事实管理", enabled=True),
        ]
        self.save()
    
    def save(self):
        """保存配置"""
        try:
            data = {
                "tools": [t.model_dump() for t in self.tools],
            }
            with open(self._config_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info("工具配置已保存")
        except Exception as e:
            logger.error(f"保存工具配置失败: {e}")
    
    def get_all_tools(self) -> List[ToolItem]:
        """获取所有工具"""
        return self.tools
    
    def get_enabled_tools(self) -> List[str]:
        """获取启用的工具 ID 列表"""
        return [t.id for t in self.tools if t.enabled]
    
    def is_enabled(self, tool_id: str) -> bool:
        """检查工具是否启用"""
        for tool in self.tools:
            if tool.id == tool_id:
                return tool.enabled
        return False
    
    def enable(self, tool_id: str):
        """启用工具"""
        for tool in self.tools:
            if tool.id == tool_id:
                tool.enabled = True
                break
    
    def disable(self, tool_id: str):
        """禁用工具"""
        for tool in self.tools:
            if tool.id == tool_id:
                tool.enabled = False
                break


# 全局实例
_tools_config: Optional[ToolsConfig] = None


def get_tools_config() -> ToolsConfig:
    """获取工具配置"""
    global _tools_config
    if _tools_config is None:
        _tools_config = ToolsConfig()
    return _tools_config
