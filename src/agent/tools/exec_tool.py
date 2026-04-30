# Exec Tool - 通用 Shell 命令执行工具
import asyncio
import os
import platform
import re
import sys

from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool

from utils import get_logger

logger = get_logger()


def _get_login_shell() -> str:
    """获取用户登录 shell 路径，用于在打包环境中正确加载 PATH。"""
    # 1. 优先用 SHELL 环境变量
    shell = os.environ.get('SHELL', '')
    if shell and os.path.isfile(shell):
        return shell
    # 2. 从 /etc/passwd 读取
    try:
        import pwd
        shell = pwd.getpwuid(os.getuid()).pw_shell
        if shell and os.path.isfile(shell):
            return shell
    except Exception:
        pass
    # 3. 兜底
    return '/bin/zsh' if os.path.isfile('/bin/zsh') else '/bin/bash'

DANGEROUS_PATTERNS = [
    r"rm\s+-rf\s+/", r"del\s+/s\s+/q\s+C:", r"format\s+C:",
    r"mkfs\.", r"dd\s+if=", r":\(\)\{\s*:\|:&\s*\};:",
    r">\s*/dev/sda",
]

MAX_OUTPUT_LENGTH = 10 * 1024


class ExecToolArgs(BaseModel):
    command: str = Field(description="要执行的 shell 命令")
    workdir: str = Field(default="", description="工作目录，默认为用户数据目录")
    timeout: int = Field(default=30, description="超时时间(秒)，最大120", ge=5, le=120)


def _is_dangerous_command(command: str) -> bool:
    cmd_lower = command.lower().strip()
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, cmd_lower):
            return True
    return False


async def exec_command(command: str, workdir: str = "", timeout: int = 30) -> str:
    if _is_dangerous_command(command):
        logger.warning(f"拦截危险命令: {command}")
        return "Error: 该命令被安全策略拦截（检测到危险操作模式）。"

    if not workdir:
        from utils.constants import DATA_DIR
        workdir = str(DATA_DIR)

    # 从 SkillsConfig 获取超时上限
    try:
        from agent.skills.config import get_skills_config
        config = get_skills_config()
        effective_timeout = min(timeout, config.exec_timeout)
    except Exception:
        effective_timeout = min(timeout, 120)
    logger.info(f"[exec] 执行: {command[:100]} (timeout={effective_timeout}s)")

    try:
        # ── 修复打包后 PATH 缺失问题 ──
        # macOS .app 启动时 PATH 极度精简，/bin/sh 不会加载 .zshrc/.zprofile，
        # 导致 node 等用户安装的命令找不到。
        # 解决方案：在打包环境中，用登录 shell (zsh -l -c) 包裹命令，
        # 这样命令能获得完整的 PATH（包括 nvm/fnm 管理的 node 路径）。
        if getattr(sys, 'frozen', False):
            login_shell = _get_login_shell()
            # 用登录 shell 执行命令，-l 加载 .zprofile/.zshrc，使 PATH 完整
            proc = await asyncio.create_subprocess_exec(
                login_shell, '-l', '-c', command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=workdir,
            )
        else:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=workdir,
            )

        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=effective_timeout)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.communicate()
            return f"Error: 命令执行超时（{effective_timeout}秒），已终止。"

        output_parts = []
        if stdout:
            output_parts.append(stdout.decode("utf-8", errors="replace"))
        if stderr:
            stderr_str = stderr.decode("utf-8", errors="replace").strip()
            if stderr_str:
                output_parts.append(f"[stderr]\n{stderr_str}")

        result = "\n".join(output_parts).strip()
        if not result:
            result = "(命令执行成功，无输出)" if proc.returncode == 0 else f"(命令退出码: {proc.returncode})"

        if proc.returncode != 0:
            result = f"(退出码: {proc.returncode})\n{result}"

        if len(result) > MAX_OUTPUT_LENGTH:
            result = result[:MAX_OUTPUT_LENGTH] + "\n... (输出已截断)"

        return result

    except FileNotFoundError as e:
        return f"Error: 命令未找到 - {e}"
    except Exception as e:
        logger.error(f"[exec] 执行错误: {e}", exc_info=True)
        return f"Error: {str(e)}"


def create_exec_tool() -> StructuredTool:
    return StructuredTool(
        name="exec",
        description=(
            "执行 shell 命令并返回输出结果。"
            "当 skill 中描述了需要执行的命令（如 curl、python3、bash 脚本等）时，使用此工具来执行。"
            "支持 bash/sh 命令，可设置工作目录和超时时间。"
        ),
        args_schema=ExecToolArgs,
        coroutine=exec_command,
    )
