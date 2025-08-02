"""Logging configuration and utilities."""

import logging
import sys
from typing import Optional

from run_a_job.config.settings import settings


def setup_logging(
    level: Optional[str] = None,
    format_string: Optional[str] = None,
) -> None:
    """Setup application logging configuration."""
    log_level = level or settings.log_level
    log_format = format_string or settings.log_format
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ]
    )
    
    # Set specific logger levels
    logging.getLogger("playwright").setLevel(logging.WARNING)
    logging.getLogger("selenium").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the specified name."""
    return logging.getLogger(name)