# Task Manager
import sys
from pathlib import Path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from typing import List, Callable, Optional
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from scheduler.task import ScheduledTask, CREATE_SCHEDULED_TASK_TOOL
from scheduler.storage import get_task_storage
from utils import get_logger

logger = get_logger()


class TaskManager:
    """定时任务管理器"""

    def __init__(self):
        self.storage = get_task_storage()
        self.scheduler = AsyncIOScheduler()
        self._on_task_execute: Optional[Callable] = None
        self._running = False

    def set_task_executor(self, executor: Callable):
        """设置任务执行回调"""
        self._on_task_execute = executor

    async def start(self):
        """启动调度器"""
        if self._running:
            return

        # 加载已保存的任务
        tasks = self.storage.list_enabled()
        for task in tasks:
            self._add_job(task)

        self.scheduler.start()
        self._running = True
        logger.info(f"定时任务管理器已启动，{len(tasks)} 个任务已加载")

    async def stop(self):
        """停止调度器"""
        if not self._running:
            return

        self.scheduler.shutdown()
        self._running = False
        logger.info("定时任务管理器已停止")

    async def create_task(
        self,
        task_name: str,
        cron: str,
        action_prompt: str,
        motion_id: Optional[str] = None
    ) -> ScheduledTask:
        """创建定时任务"""
        task = ScheduledTask(
            task_name=task_name,
            cron=cron,
            action_prompt=action_prompt,
            motion_id=motion_id
        )

        self.storage.add(task)

        if self._running:
            self._add_job(task)

        return task

    def _add_job(self, task: ScheduledTask):
        """添加 APScheduler job"""
        try:
            parts = task.cron.split()
            if len(parts) != 5:
                logger.error(f"Invalid cron expression: {task.cron}")
                return

            minute, hour, day, month, day_of_week = parts

            self.scheduler.add_job(
                self._execute_task,
                trigger=CronTrigger(
                    minute=minute,
                    hour=hour,
                    day=day,
                    month=month,
                    day_of_week=day_of_week
                ),
                args=[task.id],
                id=task.id,
                replace_existing=True
            )

            logger.info(f"已添加定时任务: {task.task_name} ({task.cron})")
        except Exception as e:
            logger.error(f"添加定时任务失败: {e}")

    async def _execute_task(self, task_id: str):
        """执行任务"""
        task = self.storage.get(task_id)
        if not task or not task.enabled:
            return

        logger.info(f"执行定时任务: {task.task_name}")

        # 更新最后运行时间
        task.last_run = datetime.utcnow()
        self.storage.update(task)

        # 调用回调
        if self._on_task_execute:
            try:
                await self._on_task_execute(task)
            except Exception as e:
                logger.error(f"任务执行回调失败: {e}")

    def list_tasks(self, only_enabled: bool = False) -> List[ScheduledTask]:
        """列出任务"""
        if only_enabled:
            return self.storage.list_enabled()
        return self.storage.list_all()

    async def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        if self._running:
            try:
                self.scheduler.remove_job(task_id)
            except Exception:
                pass

        return self.storage.delete(task_id)

    async def enable_task(self, task_id: str) -> bool:
        """启用任务"""
        task = self.storage.get(task_id)
        if task:
            task.enabled = True
            self.storage.update(task)
            if self._running:
                self._add_job(task)
            return True
        return False

    async def disable_task(self, task_id: str) -> bool:
        """禁用任务"""
        task = self.storage.get(task_id)
        if task:
            task.enabled = False
            self.storage.update(task)
            if self._running:
                try:
                    self.scheduler.remove_job(task_id)
                except Exception:
                    pass
            return True
        return False

    def get_tools(self) -> list:
        """获取工具定义"""
        return [CREATE_SCHEDULED_TASK_TOOL]


# 全局管理器实例
_manager: Optional[TaskManager] = None


def get_task_manager() -> TaskManager:
    """获取任务管理器"""
    global _manager
    if _manager is None:
        _manager = TaskManager()
    return _manager
