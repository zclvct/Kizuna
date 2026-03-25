# LLM Task Executor - LLM 驱动的任务执行器
import sys
from pathlib import Path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

import asyncio
from typing import TYPE_CHECKING
from PySide6.QtCore import QTimer

from scheduler.task import ScheduledTask
from utils import get_logger

if TYPE_CHECKING:
    from chat import ChatWidget
    from app.main_window import MainWindow

logger = get_logger()


class LLMTaskExecutor:
    """LLM 驱动的任务执行器
    
    负责：
    1. 打开对话窗口
    2. 在对话中添加任务提示
    3. 触发 LLM 执行任务
    """
    
    def __init__(self, chat_widget: "ChatWidget", main_window: "MainWindow"):
        """初始化执行器
        
        Args:
            chat_widget: 对话窗口组件
            main_window: 主窗口
        """
        self.chat_widget = chat_widget
        self.main_window = main_window
        logger.info("LLMTaskExecutor 初始化完成")
    
    async def execute_task(self, task: ScheduledTask) -> bool:
        """执行定时任务
        
        流程:
        1. 确保对话窗口可见
        2. 在对话中添加系统提示（任务触发）
        3. 触发 LLM 处理 action_prompt
        
        Args:
            task: 要执行的任务
            
        Returns:
            是否成功执行
        """
        try:
            logger.info(f"开始执行任务: {task.task_name}")
            
            # 1. 确保对话窗口可见
            if not self.main_window._chat_visible:
                logger.info("对话窗口未打开，正在打开...")
                # 在主线程中显示对话窗口
                QTimer.singleShot(0, self.main_window._show_chat)
                # 等待窗口显示
                await asyncio.sleep(0.3)
            
            # 2. 在对话中添加系统提示
            await self._add_task_prompt(task)
            
            # 3. 触发 LLM 处理
            await self._trigger_llm_response(task.action_prompt, task.task_name)
            
            logger.info(f"任务执行完成: {task.task_name}")
            return True
            
        except Exception as e:
            logger.error(f"任务执行失败: {e}", exc_info=True)
            return False
    
    async def _add_task_prompt(self, task: ScheduledTask):
        """在对话中添加任务触发提示
        
        Args:
            task: 任务对象
        """
        # 构建系统提示消息
        system_message = (
            f"⏰ 定时任务触发\n\n"
            f"📋 任务：{task.task_name}\n"
            f"🕐 时间：{task.cron}\n\n"
            f"正在执行任务..."
        )
        
        # 在主线程中添加消息气泡
        QTimer.singleShot(0, lambda: 
            self.chat_widget._add_message_bubble(system_message, is_user=False)
        )
        
        # 等待 UI 更新
        await asyncio.sleep(0.2)
    
    async def _trigger_llm_response(self, action_prompt: str, task_name: str):
        """触发 LLM 响应
        
        Args:
            action_prompt: 任务执行提示词
            task_name: 任务名称
        """
        # 构建完整的任务提示
        full_prompt = (
            f"[定时任务执行]\n"
            f"任务名称：{task_name}\n"
            f"任务内容：{action_prompt}\n\n"
            f"请执行上述任务。"
        )
        
        # 在主线程中触发 LLM 处理
        QTimer.singleShot(0, lambda: 
            self._call_llm(full_prompt)
        )
        
        logger.info(f"已触发 LLM 处理任务: {task_name}")
    
    def _call_llm(self, prompt: str):
        """调用 LLM（在主线程中执行）
        
        Args:
            prompt: 提示词
        """
        try:
            # 添加用户消息到对话历史（标记为任务触发）
            self.chat_widget.conversation_manager.add_user_message(prompt)
            
            # 直接触发生成回复
            self.chat_widget._generate_response(prompt)
            
        except Exception as e:
            logger.error(f"调用 LLM 失败: {e}", exc_info=True)
            # 添加错误提示
            error_msg = f"❌ 任务执行出错：{str(e)}"
            self.chat_widget._add_message_bubble(error_msg, is_user=False)
