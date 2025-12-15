"""
Logging Configuration
"""

import logging
import os
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from pythonjsonlogger import jsonlogger


def setup_logging(
    log_level: str = None,
    log_file: str = None,
    max_bytes: int = None,
    backup_count: int = None,
    json_format: bool = None
):
    """
    Configure logging for the application.

    Args:
        log_level: Logging level
        log_file: Path to log file
        max_bytes: Maximum log file size before rotation
        backup_count: Number of backup files to keep
        json_format: Whether to use JSON formatting
    """
    # Use environment variables as defaults
    log_level = log_level or os.getenv("LOG_LEVEL", "INFO")
    logs_dir = os.getenv("LOGS_DIR", "logs")
    log_file = log_file or f"{logs_dir}/vaas.log"
    max_bytes = max_bytes if max_bytes is not None else int(os.getenv("LOG_MAX_BYTES", "10485760"))
    backup_count = backup_count if backup_count is not None else int(os.getenv("LOG_BACKUP_COUNT", "5"))
    json_format = json_format if json_format is not None else os.getenv("LOG_JSON_FORMAT", "false").lower() == "true"
    
    # Create logs directory
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)

    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    logger.handlers.clear()

    # Format
    if json_format:
        formatter = jsonlogger.JsonFormatter(
            '%(asctime)s %(name)s %(levelname)s %(message)s'
        )
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler with rotation
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Set third-party loggers to WARNING
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

    logger.info(f"Logging configured: level={log_level}, file={log_file}")

