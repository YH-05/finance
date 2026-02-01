"""
log.py
"""

import datetime
import logging
from pathlib import Path

from debugpy.common.log import LogFile
import pandas as pd

from . import Config


def setup_logging(
    level: int = logging.INFO, log_file: str | None = None, console_output: bool = True
):
    """ロギング設定を一箇所で管理"""
    # 既存のハンドラをクリア
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    handlers = []
    log_format = "[%(asctime)s | %(funcName)s | %(levelname)s] - %(message)s"
    formatter = logging.Formatter(log_format)

    # console handler
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        handlers.append(console_handler)

    # file handler
    if log_file:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = Path(log_file)  # ty:ignore[invalid-assignment]
        stem = log_file.stem  # ty:ignore[unresolved-attribute]
        suffix = log_file.suffix  # ty:ignore[unresolved-attribute]

        config = Config.from_env()
        log_path = config.log_dir / f"{stem}_{timestamp}{suffix}"

        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)

    logging.basicConfig(
        level=level,
        format=log_format,
        handlers=handlers,
        force=True,
    )
    pd.set_option("future.no_silent_downcasting", True)
