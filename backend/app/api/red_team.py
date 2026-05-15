"""Development launcher for the standalone red-team service."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

from fastapi import APIRouter, HTTPException


router = APIRouter()

REPO_ROOT = Path(__file__).resolve().parents[3]
RED_TEAM_DIR = REPO_ROOT / "red_teaming"
DEFAULT_RED_TEAM_URL = "http://127.0.0.1:8010"
_red_team_process: subprocess.Popen | None = None


def _red_team_url() -> str:
    return os.getenv("RED_TEAM_SERVICE_URL", DEFAULT_RED_TEAM_URL).rstrip("/")


def _is_service_ready(url: str) -> bool:
    try:
        with urlopen(f"{url}/api/runs", timeout=0.75) as response:
            return 200 <= response.status < 500
    except (OSError, URLError):
        return False


def _process_is_alive() -> bool:
    return _red_team_process is not None and _red_team_process.poll() is None


@router.get("/red-team/service/status")
def red_team_service_status() -> dict[str, Any]:
    """Return whether the standalone red-team service is reachable."""
    url = _red_team_url()
    return {
        "url": url,
        "ready": _is_service_ready(url),
        "launcher_process_alive": _process_is_alive(),
    }


@router.post("/red-team/service/start")
def start_red_team_service() -> dict[str, Any]:
    """Start the standalone red-team service if it is not already reachable."""
    global _red_team_process

    url = _red_team_url()
    if _is_service_ready(url):
        return {
            "url": url,
            "ready": True,
            "started": False,
            "message": "Red-team service is already running.",
        }

    if not RED_TEAM_DIR.exists():
        raise HTTPException(status_code=500, detail="red_teaming directory was not found.")

    if not _process_is_alive():
        _red_team_process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "app.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                "8010",
            ],
            cwd=RED_TEAM_DIR,
            env={**os.environ, "PYTHONUNBUFFERED": "1"},
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    for _ in range(24):
        if _is_service_ready(url):
            return {
                "url": url,
                "ready": True,
                "started": True,
                "message": "Red-team service started.",
            }
        time.sleep(0.25)

    raise HTTPException(
        status_code=503,
        detail="Red-team service was launched but did not become ready in time.",
    )
