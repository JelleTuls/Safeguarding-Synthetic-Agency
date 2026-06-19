"""Log-inspection routes for the in-app developer console.

These endpoints expose recent backend narrative logs to the frontend. They only
return redacted, bounded output and deliberately avoid exposing raw environment
values or unrestricted files.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Query

from app.logging.live_logs import get_recent_log_entries, redact_log_text


# =============================================================================
# Router Setup
# =============================================================================

router = APIRouter()
ROOT_DIR = Path(__file__).resolve().parents[3]
RED_TEAM_SERVICE_LOG = ROOT_DIR / "red_teaming" / "data" / "logs" / "red_team_service.log"


def _tail_red_team_log(max_lines: int) -> list[dict[str, object]]:
    """Read a safe tail from the red-team service log file when it exists."""
    if max_lines <= 0 or not RED_TEAM_SERVICE_LOG.exists():
        return []
    try:
        lines = RED_TEAM_SERVICE_LOG.read_text(encoding="utf-8", errors="replace").splitlines()[-max_lines:]
    except OSError:
        return []
    entries: list[dict[str, object]] = []
    for index, line in enumerate(lines):
        cleaned = line.strip()
        if not cleaned:
            continue
        entries.append(
            {
                "id": f"red-team-file-{index}",
                "timestamp": "",
                "source": "red_team.service",
                "level": "INFO",
                "message": redact_log_text(cleaned),
            }
        )
    return entries


@router.get("/logs/recent")
async def recent_logs(limit: int = Query(default=500, ge=1, le=1600)):
    """Return recent redacted Python log lines for the frontend foldout panel."""
    memory_limit = max(1, int(limit * 0.75))
    file_limit = max(0, int(limit - memory_limit))
    entries = get_recent_log_entries(memory_limit)
    entries.extend(_tail_red_team_log(file_limit))
    return {
        "entries": entries[-limit:],
        "redacted": True,
        "sources": ["backend-memory", "red-team-service-log"],
    }
