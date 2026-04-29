# Read File Tool - 读取文件内容
from pathlib import Path

from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool

from utils import get_logger

logger = get_logger()

MAX_READ_LENGTH = 100 * 1024  # 100KB


class ReadFileArgs(BaseModel):
    path: str = Field(description="要读取的文件绝对路径")
    offset: int = Field(default=0, description="从第几行开始读取（0-based），默认从头开始")
    limit: int = Field(default=2000, description="最多读取的行数，默认2000行")


async def read_file(path: str, offset: int = 0, limit: int = 2000) -> str:
    """读取文件内容"""
    file_path = Path(path).expanduser()

    if not file_path.exists():
        return f"Error: 文件不存在 - {path}"
    if not file_path.is_file():
        return f"Error: 路径不是文件 - {path}"

    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except PermissionError:
        return f"Error: 没有读取权限 - {path}"
    except Exception as e:
        return f"Error: 读取文件失败 - {e}"

    if len(content) > MAX_READ_LENGTH:
        content = content[:MAX_READ_LENGTH] + "\n... (文件内容已截断)"

    lines = content.splitlines()

    if offset > 0 or limit < len(lines):
        selected = lines[offset:offset + limit]
        # 添加行号
        numbered = []
        for i, line in enumerate(selected, start=offset + 1):
            numbered.append(f"{i:>6}\t{line}")
        result = "\n".join(numbered)
        if offset + limit < len(lines):
            result += f"\n... (还有 {len(lines) - offset - limit} 行未显示)"
        return result

    return content


def create_read_file_tool() -> StructuredTool:
    return StructuredTool(
        name="read",
        description=(
            "读取文件内容。"
            "当需要查看 SKILL.md、脚本文件、配置文件等内容时使用此工具。"
            "支持指定行范围读取大文件。"
        ),
        args_schema=ReadFileArgs,
        coroutine=read_file,
    )
