"""Live, redacted log buffer for the frontend inspection console.

The backend normally writes its narrative trace to stdout for the terminal. This
module mirrors those records into a small in-memory ring buffer so the React app
can show recent backend activity inside the interface. Redaction happens before
records are stored or returned.
"""

from __future__ import annotations

import logging
import re
from collections import deque
from datetime import datetime, timezone
from itertools import count
from threading import Lock
from typing import Any


# =============================================================================
# Redaction And Buffer
# =============================================================================

_MAX_LOG_ENTRIES = 1600
_LOG_ENTRIES: deque[dict[str, Any]] = deque(maxlen=_MAX_LOG_ENTRIES)
_LOG_LOCK = Lock()
_LOG_ID_COUNTER = count(1)

_SECRET_PATTERNS = [
    re.compile(r"(?i)(authorization\s*[:=]\s*bearer\s+)[^\s,;]+"),
    re.compile(r"(?i)((?:api[_-]?key|access[_-]?token|secret|password)\s*[:=]\s*)[^\s,;'\"]+"),
    re.compile(r"\bsk-[A-Za-z0-9_\-]{12,}\b"),
    re.compile(r"\bgsk_[A-Za-z0-9_\-]{12,}\b"),
    re.compile(r"\b(?:eyJ[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,})\b"),
]


def redact_log_text(value: Any) -> str:
    """Return a display-safe log string with common secret shapes removed."""
    text = str(value)
    for pattern in _SECRET_PATTERNS:
        text = pattern.sub(lambda match: f"{match.group(1)}[redacted]" if match.groups() else "[redacted]", text)
    return text


def _append_entry(source: str, level: str, message: str) -> None:
    entry = {
        "id": next(_LOG_ID_COUNTER),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": redact_log_text(source),
        "level": redact_log_text(level),
        "message": redact_log_text(message),
    }
    with _LOG_LOCK:
        _LOG_ENTRIES.append(entry)


def append_external_log_line(source: str, line: str) -> None:
    """Add a line captured from a subprocess log file to the live buffer."""
    cleaned = line.strip()
    if cleaned:
        _append_entry(source, "INFO", cleaned)


def get_recent_log_entries(limit: int = 500) -> list[dict[str, Any]]:
    """Return the newest redacted log entries, oldest first."""
    safe_limit = max(1, min(int(limit or 500), _MAX_LOG_ENTRIES))
    with _LOG_LOCK:
        return list(_LOG_ENTRIES)[-safe_limit:]


# =============================================================================
# Logging Handler Installation
# =============================================================================

class LiveLogHandler(logging.Handler):
    """Logging handler that mirrors records into the live frontend buffer."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            message = self.format(record)
        except Exception:  # pragma: no cover - defensive logging guard
            message = record.getMessage()
        _append_entry(record.name, record.levelname, message)


_LIVE_HANDLER = LiveLogHandler()
_LIVE_HANDLER.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))


def attach_live_log_handler(logger: logging.Logger) -> None:
    """Attach the shared live handler to a logger once."""
    if not any(handler is _LIVE_HANDLER for handler in logger.handlers):
        logger.addHandler(_LIVE_HANDLER)


def install_live_log_capture() -> None:
    """Mirror root and server loggers into the in-app log panel."""
    for logger_name in ("", "uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
        attach_live_log_handler(logging.getLogger(logger_name))
