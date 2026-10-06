"""Logging configuration module for the Superstore data pipeline."""

import logging
import os
import sys
from pathlib import Path


def get_logger(name: str = "pipeline") -> logging.Logger:
    """Configures and returns a structured logger.

    Writes log records to both stdout and a file in logs/pipeline.log.
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    log_format = logging.Formatter(
        fmt="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)

    # File Handler
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_dir / "pipeline.log", encoding="utf-8")
    file_handler.setFormatter(log_format)
    logger.addHandler(file_handler)

    return logger
