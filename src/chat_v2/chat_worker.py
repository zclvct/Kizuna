# Chat Worker V2 - 安全的异步生成工作线程
# 改进:
# - 使用 threading.Event 安全取消，不使用 terminate()
# - 每个实例独立事件循环，不共享类级别变量
# - 更好的错误处理和日志
# - 支持流式 token 级更新（而非累积文本）
import sys
from pathlib import Path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

import asyncio
from enum import Enum, auto
from typing import Optional

from PySide6.QtCore import QThread, Signal

from agent import get_core
from agent.base_agent import ChatResponse
from utils import get_logger

logger = get_logger()


class WorkerState(Enum):
    """工作线程状态"""
    IDLE = auto()
    RUNNING = auto()
    CANCELLING = auto()
    FINISHED = auto()
    ERROR = auto()


class ChatWorker(QThread):
    """对话生成工作线程 V2

    安全取消机制:
    - 使用 threading.Event 而非 QThread.terminate()
    - 在流式迭代中检查取消标志
    - 取消后优雅退出事件循环
    """

    # ── 信号 ──
    stream_token = Signal(str)           # 单个 token 片段
    stream_accumulated = Signal(str)     # 累积的完整文本
    debug_update = Signal(dict)          # 调试信息 {debug_type, debug_title, debug_content}
    finished = Signal(dict)              # 完成 {final_text, cancelled}
    error = Signal(str)                  # 错误消息

    def __init__(self, user_text: str, core=None, is_task: bool = False, parent=None):
        super().__init__(parent)
        self.user_text = user_text
        self.core = core or get_core()
        self.is_task = is_task
        self._cancel_event = asyncio.Event()  # 取消标志
        self._state = WorkerState.IDLE
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    @property
    def state(self) -> WorkerState:
        return self._state

    def cancel(self):
        """请求取消生成（安全方式）"""
        if self._state == WorkerState.RUNNING:
            self._state = WorkerState.CANCELLING
            self._cancel_event.set()
            logger.info("用户请求取消生成")

    def run(self):
        """执行生成"""
        self._state = WorkerState.RUNNING
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

        try:
            result = self._loop.run_until_complete(self._generate())
            if self._state != WorkerState.CANCELLING:
                self._state = WorkerState.FINISHED
                self.finished.emit(result)
            else:
                self._state = WorkerState.FINISHED
                self.finished.emit({"final_text": result.get("final_text", ""), "cancelled": True})
        except Exception as e:
            self._state = WorkerState.ERROR
            logger.error(f"生成回复失败: {e}", exc_info=True)
            self.error.emit(str(e))
        finally:
            self._loop.close()
            self._loop = None

    async def _generate(self):
        """异步生成回复"""
        full_text = ""

        async for response in self.core.chat(self.user_text, stream=True):
            # 检查取消
            if self._cancel_event.is_set():
                logger.info("生成已被取消，停止流式迭代")
                break

            if response.content:
                full_text += response.content
                self.stream_token.emit(response.content)
                self.stream_accumulated.emit(full_text)

            if response.debug_type:
                self.debug_update.emit({
                    "debug_type": response.debug_type,
                    "debug_title": response.debug_title or "",
                    "debug_content": response.debug_content or "",
                })

        return {"final_text": full_text, "is_task": self.is_task, "cancelled": self._cancel_event.is_set()}
