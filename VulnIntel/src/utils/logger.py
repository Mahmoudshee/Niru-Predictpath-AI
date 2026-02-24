"""Logging configuration for VulnIntel."""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from src.config import LOG_CONFIG


def setup_logging(log_file: Path | None = None, level: str | None = None) -> None:
    """
    Configure logging for VulnIntel.
    
    Args:
        log_file: Path to log file (defaults to config LOG_CONFIG['file'])
        level: Logging level (defaults to config LOG_CONFIG['level'])
    """
    if log_file is None:
        log_file = LOG_CONFIG["file"]
    if level is None:
        level = LOG_CONFIG["level"]
    
    # Ensure log directory exists
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Create formatters
    detailed_formatter = logging.Formatter(LOG_CONFIG["format"])
    console_formatter = logging.Formatter("%(levelname)s: %(message)s")
    
    # File handler (rotating)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=LOG_CONFIG["max_bytes"],
        backupCount=LOG_CONFIG["backup_count"],
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level))
    console_handler.setFormatter(console_formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Suppress noisy third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)
