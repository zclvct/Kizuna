# Write File Tool - 写入文件内容
from pathlib import Path

from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool

from utils import get_logger

logger = get_logger()

MAX_WRITE_LENGTH = 100 * 1024  # 100KB


class WriteFileArgs(BaseModel):
    path: str = Field(description="要写入的文件绝对路径")
    content: str = Field(description="要写入的文件内容")


async def write_file(path: str, content: str) -> str:
    """写入文件内容"""
    if len(content) > MAX_WRITE_LENGTH:
        return f"Error: 内容过长（{len(content)} 字节），最大允许 {MAX_WRITE_LENGTH} 字节"

    file_path = Path(path).expanduser()

    # 安全校验：不允许写入系统关键目录
    resolved = file_path.resolve()
    critical_dirs = ["/usr", "/bin", "/sbin", "/etc", "/System", "/Library"]
    for d in critical_dirs:
        if str(resolved).startswith(d):
            return f"Error: 不允许写入系统目录 - {d}"

    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        logger.info(f"[write] 写入文件: {path} ({len(content)} 字符)")
        return f"文件写入成功: {path} ({len(content)} 字符)"
    except PermissionError:
        return f"Error: 没有写入权限 - {path}"
    except Exception as e:
        logger.error(f"[write] 写入错误: {e}", exc_info=True)
        return f"Error: 写入文件失败 - {e}"


def create_write_file_tool() -> StructuredTool:
    return StructuredTool(
        name="write",
        description=(
            "写入文件内容。"
            "当需要创建或修改脚本、配置文件等内容时使用此工具。"
            "会自动创建父目录。"
        ),
        args_schema=WriteFileArgs,
        coroutine=write_file,
    )
