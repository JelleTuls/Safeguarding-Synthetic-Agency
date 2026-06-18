"""Standalone FastAPI app for SSA red-team execution and human review."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .runner import create_run, execute_run
from .scoring import recompute_final_scores
from .storage import (
    REPORTS_DIR,
    json_report_path,
    load_run,
    list_runs,
    pdf_report_path,
    save_final_report,
    save_run,
)
from .test_suites import list_prompt_settings
from computational_analysis import ANALYSIS_ARTIFACTS
from computational_analysis import analysis_artifact_path
from computational_analysis import generate_analysis


APP_DIR = Path(__file__).resolve().parents[1]
STATIC_DIR = APP_DIR / "static"

app = FastAPI(title="SSA Red Teaming Service")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
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
    target_mode: str = "full_analysis_stack"
    profile_count: int = Field(default=1, ge=1, le=30)
    selected_profile_ids: list[str] | None = None
    expected_answer_overrides: dict[str, str] = Field(default_factory=dict)


class HumanReviewRequest(BaseModel):
    """Human mediation result for one case."""

    score: float = Field(ge=0.0, le=1.0)
    notes: str = ""


def _load_valid_final_report(path: Path) -> dict[str, Any] | None:
    """Load a final-results JSON file only when it has the expected report shape."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not payload.get("run_id") or not isinstance(payload.get("cases"), list):
        return None
    if not isinstance(payload.get("final_scores"), dict):
        return None
    return payload


def _report_summary(path: Path, report: dict[str, Any]) -> dict[str, Any]:
    """Return compact metadata for a selectable final-results JSON report."""
    final_scores = report.get("final_scores") or {}
    target_scores = final_scores.get("target_mode_scores") or {}
    return {
        "run_id": report.get("run_id"),
        "filename": path.name,
        "path": str(path),
        "created_at": report.get("created_at"),
        "completed_at": report.get("completed_at"),
        "finalized_at": report.get("finalized_at"),
        "status": report.get("status"),
        "selected_methods": report.get("selected_methods") or [],
        "target_mode": report.get("target_mode"),
        "target_modes": report.get("target_modes") or [],
        "profile_count": len(report.get("profiles") or []),
        "case_count": len(report.get("cases") or []),
        "overall_score": final_scores.get("overall_score"),
        "guardrailed_score": (target_scores.get("guardrailed") or {}).get("overall_score"),
        "lightweight_score": (target_scores.get("lightweight_no_guardrails") or {}).get("overall_score"),
        "analysis_available": analysis_artifact_path(str(report.get("run_id")), "manifest").exists(),
    }


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
        profile_count=request.profile_count,
        selected_profile_ids=request.selected_profile_ids,
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


@app.get("/api/final-reports")
def list_final_reports():
    """List saved final-results JSON files that can feed computational analysis."""
    reports: list[dict[str, Any]] = []
    for path in sorted(REPORTS_DIR.glob("*-final-results.json"), reverse=True):
        report = _load_valid_final_report(path)
        if report is None:
            continue
        reports.append(_report_summary(path, report))
    return {"reports": reports}


@app.post("/api/final-reports/{run_id}/analysis")
def generate_analysis_from_final_report(run_id: str):
    """Generate computational analysis from a saved final-results JSON report."""
    path = json_report_path(run_id)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Final report not found")
    report = _load_valid_final_report(path)
    if report is None:
        raise HTTPException(status_code=422, detail="Final report does not match the required schema")
    return generate_analysis(report)


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
        "profiles": run.get("profiles", []),
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
        "profiles": run.get("profiles", []),
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

    from datetime import datetime, timezone

    run["finalized_at"] = datetime.now(timezone.utc).isoformat()
    paths = save_final_report(run)
    run["final_report"] = {
        "json_path": str(paths["json"]),
        "pdf_path": str(paths["pdf"]),
        "download_url": f"/api/runs/{run_id}/final-report",
        "json_download_url": f"/api/runs/{run_id}/final-report",
        "pdf_download_url": f"/api/runs/{run_id}/final-report.pdf",
        "saved_at": run["finalized_at"],
    }
    save_run(run)
    return {
        "run_id": run_id,
        "final_scores": run["final_scores"],
        "final_report": run["final_report"],
    }


@app.post("/api/runs/{run_id}/analysis")
def generate_run_analysis(run_id: str):
    """Generate reproducible computational-analysis artifacts for a run."""
    try:
        run = load_run(run_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Run not found") from exc

    report_path = json_report_path(run_id)
    if report_path.exists():
        report = json.loads(report_path.read_text(encoding="utf-8"))
    else:
        run["final_scores"] = recompute_final_scores(run)
        report = run

    manifest = generate_analysis(report)
    run["computational_analysis"] = {
        "manifest": manifest,
        "generated_at": manifest.get("generated_at"),
        "download_url": f"/api/runs/{run_id}/analysis.zip",
    }
    save_run(run)
    return manifest


@app.get("/api/runs/{run_id}/analysis")
def get_run_analysis(run_id: str):
    """Return an existing analysis manifest."""
    path = analysis_artifact_path(run_id, "manifest")
    if not path.exists():
        raise HTTPException(status_code=404, detail="Analysis not generated")
    return json.loads(path.read_text(encoding="utf-8"))


@app.get("/api/runs/{run_id}/analysis.zip")
def download_run_analysis_zip(run_id: str):
    """Download all computational-analysis outputs as a zip archive."""
    path = analysis_artifact_path(run_id, "zip")
    if not path.exists():
        generate_run_analysis(run_id)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Analysis ZIP not found")
    return FileResponse(
        path,
        media_type="application/zip",
        filename=path.name,
    )


@app.get("/api/runs/{run_id}/analysis/artifacts/{artifact}")
def download_run_analysis_artifact(run_id: str, artifact: str):
    """Download one named computational-analysis artifact."""
    if artifact not in ANALYSIS_ARTIFACTS:
        raise HTTPException(status_code=404, detail="Unknown analysis artifact")
    path = analysis_artifact_path(run_id, artifact)
    if not path.exists():
        generate_run_analysis(run_id)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Analysis artifact not found")
    media_type = "text/plain"
    if path.suffix == ".svg":
        media_type = "image/svg+xml"
    elif path.suffix == ".csv":
        media_type = "text/csv"
    elif path.suffix == ".json":
        media_type = "application/json"
    return FileResponse(path, media_type=media_type, filename=path.name)


@app.get("/api/runs/{run_id}/final-report")
def download_final_report(run_id: str):
    """Download a saved final results report."""
    path = json_report_path(run_id)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Final report not found")
    return FileResponse(
        path,
        media_type="application/json",
        filename=path.name,
    )


@app.get("/api/runs/{run_id}/final-report.pdf")
def download_final_report_pdf(run_id: str):
    """Download a saved PDF-style final results report."""
    path = pdf_report_path(run_id)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Final PDF report not found")
    return FileResponse(
        path,
        media_type="application/pdf",
        filename=path.name,
    )
