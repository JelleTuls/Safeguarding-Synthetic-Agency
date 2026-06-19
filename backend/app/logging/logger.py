"""Shared stdout logger configuration for local persona chat debugging."""

import logging
import os
import sys


# =============================================================================
# Logger Configuration
# =============================================================================

_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def get_logger(name: str) -> logging.Logger:
    """Return a package logger configured to emit to stdout."""
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(_FORMAT))

    logger.addHandler(handler)
    level_name = os.getenv("SSA_LOG_LEVEL", "DEBUG").strip().upper()
    logger.setLevel(getattr(logging, level_name, logging.INFO))
    logger.propagate = False
    return logger
