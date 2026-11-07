"""插件文件日志：滚动写入插件数据目录，限制磁盘占用

单文件 512KB，保留 3 个备份，总体积上限约 2MB，写满自动滚动覆盖。
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

LOG_DIR_NAME = "logs"
LOG_FILE_NAME = "sleep_manager.log"
LOG_MAX_BYTES = 512 * 1024
LOG_BACKUP_COUNT = 3
LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"

_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
}

_file_handler: RotatingFileHandler | None = None


def setup_file_logging(logger: logging.Logger, data_dir: Any, level_name: str) -> None:
    """为插件 logger 挂滚动文件 handler；重复调用会先移除旧 handler（幂等）。"""

    global _file_handler
    shutdown_file_logging(logger)
    log_dir = Path(data_dir) / LOG_DIR_NAME
    log_dir.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(
        log_dir / LOG_FILE_NAME,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    # handler 自身放行全部级别，通过量由 logger 级别统一控制
    handler.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    target_level = _LEVELS.get(level_name, logging.INFO)
    if logger.getEffectiveLevel() > target_level:
        logger.setLevel(target_level)
    _file_handler = handler


def shutdown_file_logging(logger: logging.Logger) -> None:
    """移除并关闭文件 handler，插件卸载时调用。"""

    global _file_handler
    if _file_handler is None:
        return
    logger.removeHandler(_file_handler)
    _file_handler.close()
    _file_handler = None
