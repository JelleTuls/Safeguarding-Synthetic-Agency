"""Shared stdout and live-panel logger configuration for local debugging."""

import logging
import os
import sys

from app.logging.live_logs import attach_live_log_handler


# =============================================================================
# Logger Configuration
# =============================================================================

_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def _has_stdout_handler(logger: logging.Logger) -> bool:
    """Return whether the logger already writes to stdout."""
    return any(
        isinstance(handler, logging.StreamHandler) and getattr(handler, "stream", None) is sys.stdout
        for handler in logger.handlers
    )


def get_logger(name: str) -> logging.Logger:
    """Return a package logger configured to emit to stdout and the UI buffer."""
    logger = logging.getLogger(name)

    if not _has_stdout_handler(logger):
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(_FORMAT))
        logger.addHandler(handler)

    level_name = os.getenv("SSA_LOG_LEVEL", "DEBUG").strip().upper()
    logger.setLevel(getattr(logging, level_name, logging.INFO))
    attach_live_log_handler(logger)
    logger.propagate = False
    return logger
