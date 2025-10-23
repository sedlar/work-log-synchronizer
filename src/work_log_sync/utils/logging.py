"""Logging configuration for work log synchronizer."""

import logging
from pathlib import Path


def setup_logging(log_level: int = logging.INFO, config_dir: Path | None = None) -> None:
    """Configure logging for the application.

    Args:
        log_level: Logging level (e.g., logging.INFO, logging.DEBUG).
        config_dir: Directory to store log files. Defaults to ~/.work-log-sync/
    """
    if config_dir is None:
        config_dir = Path.home() / ".work-log-sync"

    config_dir.mkdir(parents=True, exist_ok=True)
    log_file = config_dir / "work-log-sync.log"

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(log_level)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(
        "%(name)s - %(levelname)s - %(message)s",
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Logger name (typically __name__).

    Returns:
        Logger instance.
    """
    return logging.getLogger(name)
