"""Standalone FastAPI app for SSA red-team execution and human review."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .runner import create_run, execute_run
from .scoring import recompute_final_scores
from .storage import load_run, list_runs, report_path, save_final_report, save_run
from .test_suites import list_prompt_settings


APP_DIR = Path(__file__).resolve().parents[1]
STATIC_DIR = APP_DIR / "static"

app = FastAPI(title="SSA Red Teaming Service")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class RunCreateRequest(BaseModel):
    """Request to create and start a red-team run."""

    backend_url: str = "http://127.0.0.1:8000"
    country: str = "netherlands"
    seed: int | None = None
    selected_methods: list[str] | None = None
    target_mode: str = "guardrailed"
    expected_answer_overrides: dict[str, str] = Field(default_factory=dict)


class HumanReviewRequest(BaseModel):
    """Human mediation result for one case."""

    score: float = Field(ge=0.0, le=1.0)
    notes: str = ""


@app.get("/")
def index():
    """Serve the review UI."""
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/runs")
def start_run(request: RunCreateRequest, background_tasks: BackgroundTasks):
    """Create a run and execute it in the background."""
    run = create_run(
        backend_url=request.backend_url,
        country=request.country,
        seed=request.seed,
        selected_methods=request.selected_methods,
        target_mode=request.target_mode,
        expected_answer_overrides=request.expected_answer_overrides,
    )
    save_run(run)
    background_tasks.add_task(execute_run, run)
    return {
        "run_id": run["run_id"],
        "status": run["status"],
        "backend_url": run["backend_url"],
    }


@app.get("/api/runs")
def get_runs():
    """List red-team runs."""
    return {"runs": list_runs()}


@app.get("/api/prompt-settings")
def get_prompt_settings():
    """Return red-team prompts and editable expected answer behavior."""
    return {"prompts": list_prompt_settings()}


@app.get("/api/runs/{run_id}")
def get_run(run_id: str):
    """Return a full red-team run."""
    try:
        return load_run(run_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Run not found") from exc


@app.post("/api/runs/{run_id}/cancel")
def cancel_run(run_id: str):
    """Request cancellation of a background red-team run."""
    try:
        run = load_run(run_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Run not found") from exc

    run["cancel_requested"] = True
    if run.get("status") in {"created", "running"}:
        run["status"] = "cancelling"
        progress = run.setdefault("progress", {})
        progress["current_step"] = "cancellation requested; waiting for current backend call to finish"
    save_run(run)
    return {
        "run_id": run_id,
        "status": run.get("status"),
        "cancel_requested": True,
        "progress": run.get("progress"),
    }


@app.get("/api/runs/{run_id}/review-items")
def get_review_items(run_id: str):
    """Return cases for grouped analysis and optional human review."""
    try:
        run = load_run(run_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Run not found") from exc
    cases = run.get("cases", [])
    return {
        "run_id": run_id,
        "status": run.get("status"),
        "profile": run.get("profile"),
        "final_scores": run.get("final_scores"),
        "cases": cases,
    }


@app.post("/api/runs/{run_id}/review-items/{case_id}")
def submit_review(run_id: str, case_id: str, request: HumanReviewRequest):
    """Attach a human review decision to a case and recompute final scores."""
    try:
        run = load_run(run_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Run not found") from exc

    target: dict[str, Any] | None = None
    for case in run.get("cases", []):
        if case.get("case_id") == case_id:
            target = case
            break
    if target is None:
        raise HTTPException(status_code=404, detail="Case not found")

    target["human_review"] = {
        "score": request.score,
        "passed": request.score >= 0.5,
        "notes": request.notes,
    }
    run["final_scores"] = recompute_final_scores(run)
    save_run(run)
    return {
        "case_id": case_id,
        "human_review": target["human_review"],
        "final_scores": run["final_scores"],
    }


@app.get("/api/runs/{run_id}/scores")
def get_scores(run_id: str):
    """Return current final score view."""
    try:
        run = load_run(run_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Run not found") from exc
    run["final_scores"] = recompute_final_scores(run)
    save_run(run)
    return {
        "run_id": run_id,
        "status": run.get("status"),
        "profile": run.get("profile"),
        "final_scores": run["final_scores"],
    }


@app.post("/api/runs/{run_id}/finalize")
def finalize_run(run_id: str):
    """Save a stable final results report after human mediation."""
    try:
        run = load_run(run_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Run not found") from exc

    run["final_scores"] = recompute_final_scores(run)
    if run["final_scores"].get("pending_human_reviews", 0) > 0:
        raise HTTPException(
            status_code=409,
            detail="Human review is still pending; complete mediation before saving final results.",
        )

    from datetime import datetime, timezone

    run["finalized_at"] = datetime.now(timezone.utc).isoformat()
    path = save_final_report(run)
    run["final_report"] = {
        "path": str(path),
        "download_url": f"/api/runs/{run_id}/final-report",
        "saved_at": run["finalized_at"],
    }
    save_run(run)
    return {
        "run_id": run_id,
        "final_scores": run["final_scores"],
        "final_report": run["final_report"],
    }


@app.get("/api/runs/{run_id}/final-report")
def download_final_report(run_id: str):
    """Download a saved final results report."""
    path = report_path(run_id)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Final report not found")
    return FileResponse(
        path,
        media_type="application/json",
        filename=path.name,
    )
