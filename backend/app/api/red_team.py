"""Development launcher for the standalone red-team service."""

from __future__ import annotations

import os
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import time
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen
import zlib

from fastapi import APIRouter, Body, HTTPException
from fastapi.responses import FileResponse, Response


router = APIRouter()

REPO_ROOT = Path(__file__).resolve().parents[3]
RED_TEAM_DIR = REPO_ROOT / "red_teaming"
REPORTS_DIR = RED_TEAM_DIR / "data" / "reports"
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


def _service_has_final_reports(url: str) -> bool:
    """Return true when the running service exposes the current analysis routes."""
    try:
        with urlopen(f"{url}/api/final-reports", timeout=0.75) as response:
            return 200 <= response.status < 500
    except (OSError, URLError):
        return False


def _process_is_alive() -> bool:
    return _red_team_process is not None and _red_team_process.poll() is None


def _analysis_module():
    """Import the computational-analysis module from the red_teaming package."""
    red_team_path = str(RED_TEAM_DIR)
    if red_team_path not in sys.path:
        sys.path.insert(0, red_team_path)
    import computational_analysis

    return computational_analysis


def _validate_run_id(run_id: str) -> None:
    """Reject run ids that could escape the report and analysis directories."""
    if not run_id or "/" in run_id or "\\" in run_id or ".." in run_id:
        raise HTTPException(status_code=400, detail="Invalid run id.")


def _load_valid_final_report(path: Path) -> dict[str, Any] | None:
    """Load final report JSON only if it has the required analysis schema."""
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
    """Return compact metadata for a saved final-results report."""
    analysis = _analysis_module()
    final_scores = report.get("final_scores") or {}
    target_scores = final_scores.get("target_mode_scores") or {}
    run_id = str(report.get("run_id"))
    return {
        "run_id": run_id,
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
        "analysis_available": analysis.analysis_artifact_path(run_id, "manifest").exists(),
    }


def _load_report_or_run(run_id: str) -> dict[str, Any]:
    """Load a final report when present, otherwise load the current run JSON."""
    _validate_run_id(run_id)
    report_path = REPORTS_DIR / f"{run_id}-final-results.json"
    if report_path.exists():
        report = _load_valid_final_report(report_path)
        if report is None:
            raise HTTPException(status_code=422, detail="Final report does not match the required schema.")
        return report
    run_path = RED_TEAM_DIR / "data" / "runs" / f"{run_id}.json"
    if not run_path.exists():
        raise HTTPException(status_code=404, detail="Run or final report not found.")
    return json.loads(run_path.read_text(encoding="utf-8"))


def _png_chunk(kind: bytes, data: bytes) -> bytes:
    """Return one PNG chunk with CRC."""
    return (
        struct.pack(">I", len(data))
        + kind
        + data
        + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    )


def _resize_analysis_png_bytes(path: Path, target_width: int) -> bytes:
    """Resize dependency-free RGB PNGs produced by the analysis module."""
    raw = path.read_bytes()
    signature = b"\x89PNG\r\n\x1a\n"
    if not raw.startswith(signature):
        return raw
    offset = len(signature)
    width = height = None
    idat = bytearray()
    while offset + 8 <= len(raw):
        length = struct.unpack(">I", raw[offset : offset + 4])[0]
        kind = raw[offset + 4 : offset + 8]
        data = raw[offset + 8 : offset + 8 + length]
        offset += 12 + length
        if kind == b"IHDR":
            width, height, bit_depth, color_type, compression, filter_method, interlace = struct.unpack(">IIBBBBB", data)
            if bit_depth != 8 or color_type != 2 or compression != 0 or filter_method != 0 or interlace != 0:
                return raw
        elif kind == b"IDAT":
            idat.extend(data)
        elif kind == b"IEND":
            break
    if not width or not height or target_width == width:
        return raw
    inflated = zlib.decompress(bytes(idat))
    row_bytes = width * 3
    rows: list[bytes] = []
    cursor = 0
    for _ in range(height):
        filter_type = inflated[cursor]
        if filter_type != 0:
            return raw
        cursor += 1
        rows.append(inflated[cursor : cursor + row_bytes])
        cursor += row_bytes
    target_height = max(1, round(height * target_width / width))
    scaled = bytearray()
    for y in range(target_height):
        source_y = min(height - 1, int(y * height / target_height))
        source_row = rows[source_y]
        scaled.append(0)
        for x in range(target_width):
            source_x = min(width - 1, int(x * width / target_width))
            start = source_x * 3
            scaled.extend(source_row[start : start + 3])
    ihdr = struct.pack(">IIBBBBB", target_width, target_height, 8, 2, 0, 0, 0)
    return signature + _png_chunk(b"IHDR", ihdr) + _png_chunk(b"IDAT", zlib.compress(bytes(scaled), level=9)) + _png_chunk(b"IEND", b"")


@router.get("/red-team/service/status")
def red_team_service_status() -> dict[str, Any]:
    """Return whether the standalone red-team service is reachable."""
    url = _red_team_url()
    return {
        "url": url,
        "ready": _is_service_ready(url),
        "analysis_routes_ready": _service_has_final_reports(url),
        "launcher_process_alive": _process_is_alive(),
    }


@router.post("/red-team/service/start")
def start_red_team_service() -> dict[str, Any]:
    """Start the standalone red-team service if it is not already reachable."""
    global _red_team_process

    url = _red_team_url()
    if _is_service_ready(url) and _service_has_final_reports(url):
        return {
            "url": url,
            "ready": True,
            "started": False,
            "message": "Red-team service is already running.",
        }
    if _is_service_ready(url) and not _service_has_final_reports(url) and _process_is_alive():
        _red_team_process.terminate()
        try:
            _red_team_process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            _red_team_process.kill()

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
        if _is_service_ready(url) and _service_has_final_reports(url):
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


@router.get("/red-team/final-reports")
def list_final_reports() -> dict[str, Any]:
    """List saved final-results JSON files eligible for computational analysis."""
    reports: list[dict[str, Any]] = []
    if not REPORTS_DIR.exists():
        return {"reports": reports}
    for path in sorted(REPORTS_DIR.glob("*-final-results.json"), reverse=True):
        report = _load_valid_final_report(path)
        if report is None:
            continue
        reports.append(_report_summary(path, report))
    return {"reports": reports}


@router.post("/red-team/final-reports/{run_id}/analysis")
def generate_analysis_from_final_report(run_id: str, config: dict[str, Any] | None = Body(default=None)) -> dict[str, Any]:
    """Generate computational analysis directly from a saved final report."""
    _validate_run_id(run_id)
    report_path = REPORTS_DIR / f"{run_id}-final-results.json"
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Final report not found.")
    report = _load_valid_final_report(report_path)
    if report is None:
        raise HTTPException(status_code=422, detail="Final report does not match the required schema.")
    return _analysis_module().generate_analysis(report, config=config)


@router.get("/red-team/final-reports/{run_id}/json")
def download_final_report_json(run_id: str):
    """Download the complete saved final-results JSON dataset."""
    _validate_run_id(run_id)
    report_path = REPORTS_DIR / f"{run_id}-final-results.json"
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Final report not found.")
    return FileResponse(
        report_path,
        media_type="application/json",
        filename=report_path.name,
    )


@router.get("/red-team/final-reports/{run_id}/pdf")
def download_final_report_pdf(run_id: str):
    """Download the saved final-results PDF report."""
    _validate_run_id(run_id)
    report_path = REPORTS_DIR / f"{run_id}-final-results.pdf"
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Final report PDF not found.")
    return FileResponse(
        report_path,
        media_type="application/pdf",
        filename=report_path.name,
    )


@router.delete("/red-team/final-reports/{run_id}")
def delete_final_report(run_id: str) -> dict[str, Any]:
    """Delete a saved final-results JSON report, its PDF, and generated analysis."""
    _validate_run_id(run_id)
    json_path = REPORTS_DIR / f"{run_id}-final-results.json"
    pdf_path = REPORTS_DIR / f"{run_id}-final-results.pdf"
    if not json_path.exists():
        raise HTTPException(status_code=404, detail="Final report not found.")

    deleted: list[str] = []
    for path in (json_path, pdf_path):
        if path.exists():
            path.unlink()
            deleted.append(str(path))

    analysis_dir = _analysis_module().analysis_output_dir(run_id)
    if analysis_dir.exists():
        shutil.rmtree(analysis_dir)
        deleted.append(str(analysis_dir))

    return {
        "run_id": run_id,
        "deleted": deleted,
    }


@router.post("/red-team/runs/{run_id}/analysis")
def generate_run_analysis(run_id: str, config: dict[str, Any] | None = Body(default=None)) -> dict[str, Any]:
    """Generate computational analysis from a run or its saved final report."""
    _validate_run_id(run_id)
    return _analysis_module().generate_analysis(_load_report_or_run(run_id), config=config)


@router.get("/red-team/runs/{run_id}/analysis")
def get_run_analysis(run_id: str) -> dict[str, Any]:
    """Return an existing computational-analysis manifest."""
    _validate_run_id(run_id)
    analysis = _analysis_module()
    path = analysis.analysis_artifact_path(run_id, "manifest")
    if not path.exists():
        raise HTTPException(status_code=404, detail="Analysis not generated.")
    return json.loads(path.read_text(encoding="utf-8"))


@router.get("/red-team/runs/{run_id}/analysis.zip")
def download_run_analysis_zip(run_id: str):
    """Download the computational-analysis artifact bundle."""
    _validate_run_id(run_id)
    analysis = _analysis_module()
    path = analysis.analysis_artifact_path(run_id, "zip")
    if not path.exists():
        analysis.generate_analysis(_load_report_or_run(run_id))
    return FileResponse(path, media_type="application/zip", filename=path.name)


@router.get("/red-team/runs/{run_id}/analysis/artifacts/{artifact}")
def download_run_analysis_artifact(run_id: str, artifact: str):
    """Download one named computational-analysis artifact."""
    _validate_run_id(run_id)
    analysis = _analysis_module()
    if artifact not in analysis.ANALYSIS_ARTIFACTS:
        raise HTTPException(status_code=404, detail="Unknown analysis artifact.")
    path = analysis.analysis_artifact_path(run_id, artifact)
    if not path.exists():
        analysis.generate_analysis(_load_report_or_run(run_id))
    media_type = "text/plain"
    if path.suffix == ".svg":
        media_type = "image/svg+xml"
    elif path.suffix == ".csv":
        media_type = "text/csv"
    elif path.suffix == ".json":
        media_type = "application/json"
    elif path.suffix == ".pdf":
        media_type = "application/pdf"
    elif path.suffix == ".png":
        media_type = "image/png"
    elif path.suffix == ".zip":
        media_type = "application/zip"
    return FileResponse(path, media_type=media_type, filename=path.name)


@router.get("/red-team/runs/{run_id}/analysis/plots/{artifact}.png")
def download_run_analysis_plot_png(run_id: str, artifact: str, width: int = 1800):
    """Download a generated PNG plot without relying on browser canvas export."""
    _validate_run_id(run_id)
    analysis = _analysis_module()
    manifest_path = analysis.analysis_artifact_path(run_id, "manifest")
    if not manifest_path.exists():
        analysis.generate_analysis(_load_report_or_run(run_id))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    figure = (manifest.get("figures") or {}).get(artifact)
    if not figure or figure.get("skipped"):
        raise HTTPException(status_code=404, detail="Plot PNG is not available.")
    png_path = Path((manifest.get("png_files") or {}).get(artifact, ""))
    if not png_path.exists() or not png_path.is_file():
        analysis.generate_analysis(_load_report_or_run(run_id))
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        png_path = Path((manifest.get("png_files") or {}).get(artifact, ""))
    if not png_path.exists() or not png_path.is_file():
        raise HTTPException(status_code=404, detail="Plot PNG is not available.")
    safe_width = min(max(int(width or 1800), 300), 5000)
    filename = f"{run_id}-{artifact}-{safe_width}px.png"
    png_bytes = _resize_analysis_png_bytes(png_path, safe_width)
    return Response(
        png_bytes,
        media_type="image/png",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
