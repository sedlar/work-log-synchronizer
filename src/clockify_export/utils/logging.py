# ABOUTME: Logging configuration for clockify-export.
# ABOUTME: Sets up file and console log handlers.

import logging
from pathlib import Path

CONFIG_DIR_NAME = "clockify-export"


def setup_logging(log_level: int = logging.INFO, config_dir: Path | None = None) -> None:
    """Configure logging for the application."""
    if config_dir is None:
        config_dir = Path.home() / ".config" / CONFIG_DIR_NAME

    config_dir.mkdir(parents=True, exist_ok=True)
    log_file = config_dir / "clockify-export.log"

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(log_level)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(
        "%(name)s - %(levelname)s - %(message)s",
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)
