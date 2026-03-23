# Task Execution History
import sys
from pathlib import Path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from typing import List, Dict, Optional
import json
from datetime import datetime
from pydantic import BaseModel, Field

from utils import get_logger

logger = get_logger()


class TaskExecutionRecord(BaseModel):
    """任务执行记录"""
    id: str = Field(default_factory=lambda: str(datetime.utcnow().timestamp()))
    task_id: str
    task_name: str
    executed_at: datetime = Field(default_factory=datetime.utcnow)
    success: bool
    result: Optional[str] = None
    error: Optional[str] = None
    duration_seconds: Optional[float] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TaskHistoryManager:
    """任务执行历史管理器"""

    def __init__(self, file_path: Optional[Path] = None):
        if file_path is None:
            from utils import DATA_DIR
            file_path = DATA_DIR / "task_history.json"

        self.file_path = file_path
        self._records: List[TaskExecutionRecord] = []
        self._load()

    def _load(self):
        """从文件加载历史记录"""
        if not self.file_path.exists():
            return

        try:
            data = json.loads(self.file_path.read_text(encoding="utf-8"))
            for record_data in data.get("records", []):
                # 转换 datetime 字符串
                if record_data.get("executed_at"):
                    record_data["executed_at"] = datetime.fromisoformat(record_data["executed_at"])

                record = TaskExecutionRecord(**record_data)
                self._records.append(record)

            logger.info(f"已加载 {len(self._records)} 条执行记录")
        except Exception as e:
            logger.error(f"加载执行记录失败: {e}")

    def _save(self):
        """保存历史记录到文件"""
        data = {
            "records": [
                {
                    "id": r.id,
                    "task_id": r.task_id,
                    "task_name": r.task_name,
                    "executed_at": r.executed_at.isoformat(),
                    "success": r.success,
                    "result": r.result,
                    "error": r.error,
                    "duration_seconds": r.duration_seconds
                }
                for r in self._records
            ]
        }
        self.file_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

    def add_record(
        self,
        task_id: str,
        task_name: str,
        success: bool,
        result: Optional[str] = None,
        error: Optional[str] = None,
        duration_seconds: Optional[float] = None
    ) -> TaskExecutionRecord:
        """添加执行记录"""
        record = TaskExecutionRecord(
            task_id=task_id,
            task_name=task_name,
            success=success,
            result=result,
            error=error,
            duration_seconds=duration_seconds
        )
        self._records.append(record)
        self._save()
        logger.info(f"已记录任务执行: {task_name} - {'成功' if success else '失败'}")
        return record

    def get_task_history(self, task_id: str, limit: int = 100) -> List[TaskExecutionRecord]:
        """获取指定任务的历史记录"""
        records = [r for r in self._records if r.task_id == task_id]
        return sorted(records, key=lambda r: r.executed_at, reverse=True)[:limit]

    def get_all_history(self, limit: int = 1000) -> List[TaskExecutionRecord]:
        """获取所有历史记录"""
        return sorted(self._records, key=lambda r: r.executed_at, reverse=True)[:limit]

    def get_statistics(self, task_id: Optional[str] = None) -> Dict:
        """获取统计信息"""
        records = self._records
        if task_id:
            records = [r for r in records if r.task_id == task_id]

        total = len(records)
        success_count = sum(1 for r in records if r.success)
        failure_count = total - success_count
        success_rate = (success_count / total * 100) if total > 0 else 0

        avg_duration = None
        durations = [r.duration_seconds for r in records if r.duration_seconds is not None]
        if durations:
            avg_duration = sum(durations) / len(durations)

        return {
            "total_executions": total,
            "success_count": success_count,
            "failure_count": failure_count,
            "success_rate": round(success_rate, 2),
            "average_duration": round(avg_duration, 2) if avg_duration else None
        }

    def clear_old_records(self, days: int = 30):
        """清理旧的执行记录"""
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(days=days)

        old_count = len(self._records)
        self._records = [r for r in self._records if r.executed_at > cutoff]
        new_count = len(self._records)

        if old_count != new_count:
            self._save()
            logger.info(f"已清理 {old_count - new_count} 条旧记录 (超过 {days} 天)")


# 全局历史管理器实例
_history_manager: Optional[TaskHistoryManager] = None


def get_task_history_manager() -> TaskHistoryManager:
    """获取任务历史管理器"""
    global _history_manager
    if _history_manager is None:
        _history_manager = TaskHistoryManager()
    return _history_manager
