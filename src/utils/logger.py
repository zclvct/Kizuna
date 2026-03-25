# Logger Setup
import logging
import sys
from pathlib import Path

from .constants import DATA_DIR

LOG_FILE = DATA_DIR / "app.log"

_logger = None


def setup_logger(level: int = logging.INFO) -> logging.Logger:
    """设置 logger"""
    global _logger

    if _logger is not None:
        return _logger

    logger = logging.getLogger("Kizuna")
    logger.setLevel(level)

    # 避免重复添加 handler
    if logger.handlers:
        _logger = logger
        return logger

    # 格式
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 文件 handler
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # 控制台 handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    _logger = logger
    return logger


def get_logger() -> logging.Logger:
    """获取 logger"""
    if _logger is None:
        return setup_logger()
    return _logger
