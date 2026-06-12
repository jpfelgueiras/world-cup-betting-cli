"""
Structured logging utility for World Cup Betting Insights CLI

Provides consistent logging across scrapers, API, and CLI components.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str,
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    structured: bool = False,
) -> logging.Logger:
    """
    Set up a logger with console and optional file handlers.

    Args:
        name: Logger name (typically __name__)
        level: Logging level (default: INFO)
        log_file: Optional path to log file
        structured: If True, use JSON formatting for logs

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger

    # Create formatter
    formatter: logging.Formatter
    if structured:
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


class StructuredFormatter(logging.Formatter):
    """JSON-formatted log formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON-like structure."""
        timestamp = datetime.fromtimestamp(record.created).isoformat()
        return (
            f'{{"timestamp": "{timestamp}", '
            f'"level": "{record.levelname}", '
            f'"logger": "{record.name}", '
            f'"message": "{record.getMessage()}"}}'
        )


# Default logger for the application
default_logger = setup_logger("worldcup")


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    return setup_logger(name)
