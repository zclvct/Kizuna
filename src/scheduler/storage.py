# Task Storage
import sys
from pathlib import Path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from typing import List, Dict, Optional
import json
from datetime import datetime

from scheduler.task import ScheduledTask
from utils import SCHEDULED_TASKS_FILE, get_logger

logger = get_logger()


class TaskStorage:
    """任务持久化存储"""

    def __init__(self, file_path: Path = SCHEDULED_TASKS_FILE):
        self.file_path = file_path
        self._tasks: Dict[str, ScheduledTask] = {}
        self._load()

    def _load(self):
        """从文件加载任务"""
        if not self.file_path.exists():
            return

        try:
            data = json.loads(self.file_path.read_text(encoding="utf-8"))
            for task_data in data.get("tasks", []):
                # 转换 datetime 字符串
                for field in ["created_at", "last_run", "next_run"]:
                    if task_data.get(field):
                        task_data[field] = datetime.fromisoformat(task_data[field])

                task = ScheduledTask(**task_data)
                self._tasks[task.id] = task

            logger.info(f"已加载 {len(self._tasks)} 个定时任务")
        except Exception as e:
            logger.error(f"加载定时任务失败: {e}")

    def _save(self):
        """保存任务到文件"""
        data = {
            "tasks": [
                self._task_to_dict(task)
                for task in self._tasks.values()
            ]
        }
        self.file_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

    def _task_to_dict(self, task: ScheduledTask) -> Dict:
        """转换任务为字典"""
        data = task.model_dump()
        for field in ["created_at", "last_run", "next_run"]:
            if data.get(field):
                data[field] = data[field].isoformat()
        return data

    def add(self, task: ScheduledTask) -> bool:
        """添加任务"""
        self._tasks[task.id] = task
        self._save()
        logger.info(f"已添加定时任务: {task.task_name}")
        return True

    def get(self, task_id: str) -> Optional[ScheduledTask]:
        """获取任务"""
        return self._tasks.get(task_id)

    def list_all(self) -> List[ScheduledTask]:
        """列出所有任务"""
        return list(self._tasks.values())

    def list_enabled(self) -> List[ScheduledTask]:
        """列出启用的任务"""
        return [t for t in self._tasks.values() if t.enabled]

    def update(self, task: ScheduledTask) -> bool:
        """更新任务"""
        if task.id not in self._tasks:
            return False
        self._tasks[task.id] = task
        self._save()
        return True

    def delete(self, task_id: str) -> bool:
        """删除任务"""
        if task_id not in self._tasks:
            return False
        del self._tasks[task_id]
        self._save()
        logger.info(f"已删除定时任务: {task_id}")
        return True

    def enable(self, task_id: str) -> bool:
        """启用任务"""
        task = self._tasks.get(task_id)
        if task:
            task.enabled = True
            self._save()
            return True
        return False

    def disable(self, task_id: str) -> bool:
        """禁用任务"""
        task = self._tasks.get(task_id)
        if task:
            task.enabled = False
            self._save()
            return True
        return False


# 全局存储实例
_storage: Optional[TaskStorage] = None


def get_task_storage() -> TaskStorage:
    """获取任务存储"""
    global _storage
    if _storage is None:
        _storage = TaskStorage()
    return _storage
