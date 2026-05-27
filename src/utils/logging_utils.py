"""
logging_utils.py
----------------
Centralised logging factory for the Olist pipeline.
Creates a consistent logger with file + console handlers.
"""

import logging
import sys
from pathlib import Path

from src.utils.config import LOG_LEVEL, LOG_DIR


def get_logger(name: str, log_file: str | None = None) -> logging.Logger:
    """
    Create and return a configured logger.

    Parameters
    ----------
    name : str
        Logger name (typically __name__ of the calling module).
    log_file : str | None
        Optional filename (relative to LOG_DIR) to write logs to.
        If None, logs are only written to stdout.

    Returns
    -------
    logging.Logger
        Configured logger instance.
    """
    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # ── Console handler ───────────────────────
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    # ── File handler (optional) ───────────────
    if log_file:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(LOG_DIR / log_file, encoding="utf-8")
        fh.setFormatter(fmt)
        logger.addHandler(fh)

    return logger
