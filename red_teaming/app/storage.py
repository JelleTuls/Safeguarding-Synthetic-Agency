"""JSON persistence for red-team runs."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[1]
RUNS_DIR = BASE_DIR / "data" / "runs"
REPORTS_DIR = BASE_DIR / "data" / "reports"
RUNS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def run_path(run_id: str) -> Path:
    """Return the JSON path for a run id."""
    return RUNS_DIR / f"{run_id}.json"


def save_run(run: dict[str, Any]) -> None:
    """Atomically persist a run payload."""
    path = run_path(run["run_id"])
    with NamedTemporaryFile("w", delete=False, dir=RUNS_DIR, encoding="utf-8") as tmp:
        json.dump(run, tmp, indent=2, sort_keys=True)
        tmp_path = Path(tmp.name)
    tmp_path.replace(path)


def load_run(run_id: str) -> dict[str, Any]:
    """Load a run payload."""
    with run_path(run_id).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def list_runs() -> list[dict[str, Any]]:
    """Return compact summaries for all known runs."""
    runs: list[dict[str, Any]] = []
    for path in sorted(RUNS_DIR.glob("*.json"), reverse=True):
        try:
            run = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        runs.append(
            {
                "run_id": run.get("run_id"),
                "status": run.get("status"),
                "created_at": run.get("created_at"),
                "completed_at": run.get("completed_at"),
                "backend_url": run.get("backend_url"),
                "profile_label": run.get("profile", {}).get("label"),
                "profile_id": run.get("profile", {}).get("id"),
                "overall_score": run.get("final_scores", {}).get("overall_score"),
                "pending_human_reviews": run.get("final_scores", {}).get("pending_human_reviews"),
            }
        )
    return runs


def report_path(run_id: str) -> Path:
    """Return the JSON final-report path for a run id."""
    return REPORTS_DIR / f"{run_id}-final-results.json"


def save_final_report(run: dict[str, Any]) -> Path:
    """Persist a stable final report derived from a reviewed run."""
    report = {
        "run_id": run.get("run_id"),
        "status": run.get("status"),
        "created_at": run.get("created_at"),
        "completed_at": run.get("completed_at"),
        "finalized_at": run.get("finalized_at"),
        "backend_url": run.get("backend_url"),
        "country": run.get("country"),
        "target_mode": run.get("target_mode"),
        "guardrails_enabled": run.get("guardrails_enabled"),
        "selected_methods": run.get("selected_methods"),
        "profile": run.get("profile"),
        "framework": run.get("framework"),
        "final_scores": run.get("final_scores"),
        "cases": run.get("cases", []),
    }
    path = report_path(run["run_id"])
    with NamedTemporaryFile("w", delete=False, dir=REPORTS_DIR, encoding="utf-8") as tmp:
        json.dump(report, tmp, indent=2, sort_keys=True)
        tmp_path = Path(tmp.name)
    tmp_path.replace(path)
    return path
