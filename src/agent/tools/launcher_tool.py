# Launcher Tool
import subprocess
import sys
import os
from typing import Dict, Any, Optional, List
from pathlib import Path
from functools import lru_cache

from utils import get_logger

logger = get_logger()


def _normalize_app_name(name: str) -> str:
    text = (name or "").strip().lower()
    if text.endswith(".app"):
        text = text[:-4]
    if text.endswith(".exe"):
        text = text[:-4]
    return "".join(ch for ch in text if ch not in " _-")


@lru_cache(maxsize=1)
def _list_macos_apps() -> List[Path]:
    app_dirs = [
        Path("/Applications"),
        Path("/System/Applications"),
        Path.home() / "Applications",
    ]
    apps: List[Path] = []
    for app_dir in app_dirs:
        if not app_dir.exists():
            continue
        try:
            apps.extend(app_dir.rglob("*.app"))
        except Exception as e:
            logger.warning(f"扫描应用目录失败 {app_dir}: {e}")
    return apps


def _resolve_macos_app(query: str) -> Optional[Path]:
    target = _normalize_app_name(query)
    if not target:
        return None

    exact_match = None
    prefix_match = None
    contains_match = None

    for app_path in _list_macos_apps():
        app_stem = app_path.stem
        normalized = _normalize_app_name(app_stem)

        if normalized == target:
            exact_match = app_path
            break
        if prefix_match is None and normalized.startswith(target):
            prefix_match = app_path
        if contains_match is None and target in normalized:
            contains_match = app_path

    return exact_match or prefix_match or contains_match


def _resolve_windows_app(query: str) -> Optional[str]:
    target = _normalize_app_name(query)
    if not target:
        return None

    probes = [query]
    if not query.lower().endswith(".exe"):
        probes.append(f"{query}.exe")
    probes.append(f"*{query}*.exe")

    candidates: List[str] = []
    for probe in probes:
        try:
            result = subprocess.run(
                ["where", probe],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0 and result.stdout:
                for line in result.stdout.splitlines():
                    line = line.strip()
                    if line:
                        candidates.append(line)
        except Exception:
            continue

    if not candidates:
        return None

    seen = set()
    ordered_candidates = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            ordered_candidates.append(c)

    exact_match = None
    prefix_match = None
    contains_match = None

    for candidate in ordered_candidates:
        stem = Path(candidate).stem
        normalized = _normalize_app_name(stem)

        if normalized == target:
            exact_match = candidate
            break
        if prefix_match is None and normalized.startswith(target):
            prefix_match = candidate
        if contains_match is None and target in normalized:
            contains_match = candidate

    return exact_match or prefix_match or contains_match


async def open_application(app_name: str) -> Dict[str, Any]:
    """打开应用或文件（支持 macOS / Windows 模糊匹配应用名）"""
    try:
        if sys.platform == "darwin":  # macOS
            resolved = _resolve_macos_app(app_name)
            launch_candidates = []

            if resolved is not None:
                launch_candidates.append(["open", "-a", str(resolved)])
            launch_candidates.append(["open", "-a", app_name])
            launch_candidates.append(["open", app_name])

            last_error = None
            for cmd in launch_candidates:
                try:
                    subprocess.run(cmd, check=True)
                    return {
                        "app_name": app_name,
                        "resolved_app": str(resolved) if resolved else app_name,
                        "success": True,
                    }
                except Exception as e:
                    last_error = e

            raise last_error or RuntimeError("未知错误")

        elif sys.platform == "win32":  # Windows
            resolved = _resolve_windows_app(app_name)
            last_error = None

            if resolved:
                try:
                    os.startfile(resolved)
                    return {
                        "app_name": app_name,
                        "resolved_app": resolved,
                        "success": True,
                    }
                except Exception as e:
                    last_error = e

            try:
                os.startfile(app_name)
                return {
                    "app_name": app_name,
                    "resolved_app": app_name,
                    "success": True,
                }
            except Exception as e:
                last_error = e

            subprocess.run(["cmd", "/c", "start", "", app_name], check=True)
            return {
                "app_name": app_name,
                "resolved_app": resolved or app_name,
                "success": True,
            }
        else:  # Linux
            subprocess.run(["xdg-open", app_name], check=True)

        return {
            "app_name": app_name,
            "success": True
        }
    except Exception as e:
        logger.error(f"打开应用失败: {e}")
        return {
            "app_name": app_name,
            "error": str(e),
            "success": False
        }


# 工具定义
LAUNCHER_TOOL = {
    "type": "function",
    "function": {
        "name": "open_application",
        "description": "打开应用程序或文件",
        "parameters": {
            "type": "object",
            "properties": {
                "app_name": {
                    "type": "string",
                    "description": "应用名称或文件路径"
                }
            },
            "required": ["app_name"]
        }
    }
}
