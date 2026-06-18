"""JSON persistence for red-team runs."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import NamedTemporaryFile
import textwrap
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
                "profile_count": len(run.get("profiles") or []),
                "overall_score": run.get("final_scores", {}).get("overall_score"),
                "human_review_markers": run.get("final_scores", {}).get("human_review_markers"),
            }
        )
    return runs


def json_report_path(run_id: str) -> Path:
    """Return the JSON final-report path for a run id."""
    return REPORTS_DIR / f"{run_id}-final-results.json"


def pdf_report_path(run_id: str) -> Path:
    """Return the PDF final-report path for a run id."""
    return REPORTS_DIR / f"{run_id}-final-results.pdf"


def _case_final_score(case: dict[str, Any]) -> float:
    review = case.get("human_review") or {}
    value = review.get("score", case.get("automated_score", 0.0))
    return float(value if value is not None else 0.0)


def _format_percent(value: Any) -> str:
    try:
        return f"{float(value) * 100:.0f}%"
    except (TypeError, ValueError):
        return "0%"


def _short_text(value: Any, *, width: int = 220) -> str:
    """Return compact single-line text for report comparison rows."""
    text = " ".join(str(value or "").split())
    return textwrap.shorten(text, width=width, placeholder="...")


def _eb_comparison_lines(cases: list[dict[str, Any]]) -> list[str]:
    """Build a thesis-facing EB comparison section from paired target-mode cases."""
    examples = _eb_comparison_examples(cases)
    if not examples:
        return []
    lines = [
        "",
        "Epistemic Boundary Comparison Examples",
        "These paired cases show whether the guardrailed answer better matches the profile's plausible epistemic range.",
    ]
    for example in examples:
        lines.extend(
            [
                "",
                f"{example['prompt_id']} | {example['profile_label']}",
                f"Prompt: {_short_text(example['prompt'], width=260)}",
                f"Lightweight: {_format_percent(example['lightweight_score'])} | {_short_text(example['lightweight_response'])}",
                f"Guardrailed: {_format_percent(example['guardrailed_score'])} | {_short_text(example['guardrailed_response'])}",
            ]
        )
        if example.get("comparison_reason"):
            lines.append(f"Pairwise reason: {_short_text(example.get('comparison_reason'), width=280)}")
    return lines


def _eb_comparison_examples(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return structured paired EB examples for JSON reports."""
    pair_map: dict[tuple[str, str], dict[str, dict[str, Any]]] = {}
    for case in cases:
        if case.get("method") != "EB":
            continue
        key = (str(case.get("profile_id") or "profile"), str(case.get("prompt_id") or "prompt"))
        pair_map.setdefault(key, {})[case.get("target_mode") or "guardrailed"] = case

    examples: list[dict[str, Any]] = []
    for (_profile_id, prompt_id), pair in sorted(pair_map.items(), key=lambda item: item[0][1]):
        lightweight = pair.get("lightweight_no_guardrails")
        guardrailed = pair.get("guardrailed")
        if not lightweight or not guardrailed:
            continue
        comparison = guardrailed.get("comparison_grade") or lightweight.get("comparison_grade") or {}
        examples.append(
            {
                "profile_id": guardrailed.get("profile_id") or lightweight.get("profile_id"),
                "profile_label": guardrailed.get("profile_label") or lightweight.get("profile_label"),
                "prompt_id": prompt_id,
                "prompt": guardrailed.get("message") or lightweight.get("message"),
                "lightweight_score": _case_final_score(lightweight),
                "guardrailed_score": _case_final_score(guardrailed),
                "lightweight_response": lightweight.get("response_text"),
                "guardrailed_response": guardrailed.get("response_text"),
                "comparison_reason": comparison.get("comparison_reason"),
                "lightweight_metrics": ((lightweight.get("comparison_grade") or {}).get("selected_mode_result") or {}).get("metrics"),
                "guardrailed_metrics": ((guardrailed.get("comparison_grade") or {}).get("selected_mode_result") or {}).get("metrics"),
            }
        )
    return examples


def _report_lines(report: dict[str, Any]) -> list[str]:
    scores = report.get("final_scores") or {}
    lines = [
        "SSA Red-Team Final Report",
        "",
        f"Run ID: {report.get('run_id')}",
        f"Status: {report.get('status')}",
        f"Created: {report.get('created_at')}",
        f"Completed: {report.get('completed_at')}",
        f"Finalized: {report.get('finalized_at')}",
        f"Target mode: {report.get('target_mode')}",
        f"Target modes executed: {', '.join(report.get('target_modes') or [])}",
        f"Selected methods: {', '.join(report.get('selected_methods') or [])}",
        f"Selected profiles: {len(report.get('profiles') or [])}",
        f"Overall score: {_format_percent(scores.get('overall_score'))}",
        f"Average profile score: {_format_percent(scores.get('average_profile_score'))}",
        f"Human review markers: {scores.get('human_review_markers', 0)}",
        f"Human overrides saved: {scores.get('completed_human_reviews', 0)}",
        "",
        "Method Scores",
    ]
    for method, value in sorted((scores.get("method_scores") or {}).items()):
        lines.append(f"- {method}: {_format_percent(value)}")

    if scores.get("target_mode_scores"):
        lines.extend(["", "Target Mode Scores"])
        for mode, value in sorted(scores.get("target_mode_scores", {}).items()):
            lines.append(f"- {mode}: {_format_percent(value.get('overall_score'))}")
    if scores.get("guardrail_improvement"):
        improvement = scores["guardrail_improvement"]
        lines.extend([
            "",
            "Guardrail Improvement",
            f"Overall delta: {_format_percent(improvement.get('overall_delta'))}",
            f"Guardrailed score: {_format_percent(improvement.get('guardrailed_score'))}",
            f"Lightweight score: {_format_percent(improvement.get('lightweight_score'))}",
        ])

    lines.extend(_eb_comparison_lines(report.get("cases", [])))

    lines.extend(["", "Profile Scores"])
    for profile_id, profile_score in sorted((scores.get("profile_scores") or {}).items()):
        lines.append(
            f"- {profile_score.get('profile_label') or profile_id}: "
            f"{_format_percent(profile_score.get('overall_score'))} "
            f"({profile_score.get('case_count', 0)} cases)"
        )
        for method, value in sorted((profile_score.get("method_scores") or {}).items()):
            lines.append(f"    {method}: {_format_percent(value)}")

    lines.extend(["", "Case Overview"])
    for case in report.get("cases", []):
        lines.extend(
            [
                "",
                f"{case.get('profile_label')} | {case.get('prompt_id')} | {case.get('method_name')}",
                f"Target mode: {case.get('target_mode')}",
                f"Final score: {_format_percent(_case_final_score(case))} "
                f"(auto {_format_percent(case.get('automated_score'))})",
                f"Individual LLM score: {_format_percent(case.get('llm_score'))}",
                f"Pairwise comparison score: {_format_percent(case.get('comparison_score'))}",
                f"Prompt: {case.get('message', '')}",
                f"Expected behavior: {case.get('expected_answer', '')}",
                f"Expected style: {case.get('expected_response_style', '')}",
                f"Response: {case.get('response_text', '')}",
            ]
        )
        review = case.get("human_review") or {}
        if review:
            lines.append(f"Human notes: {review.get('notes', '')}")
    return lines


def _pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _write_simple_pdf(path: Path, lines: list[str]) -> None:
    """Write a compact plain-text PDF without external dependencies."""
    wrapped: list[str] = []
    for line in lines:
        if not line:
            wrapped.append("")
            continue
        wrapped.extend(textwrap.wrap(str(line), width=96) or [""])

    pages = [wrapped[index : index + 48] for index in range(0, len(wrapped), 48)] or [[]]
    objects: list[str] = []
    objects.append("<< /Type /Catalog /Pages 2 0 R >>")
    kids = " ".join(f"{3 + page_index * 2} 0 R" for page_index in range(len(pages)))
    objects.append(f"<< /Type /Pages /Kids [{kids}] /Count {len(pages)} >>")

    for page_index, page_lines in enumerate(pages):
        page_obj = 3 + page_index * 2
        content_obj = page_obj + 1
        objects.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Resources << /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> >> >> "
            f"/Contents {content_obj} 0 R >>"
        )
        text_ops = ["BT", "/F1 9 Tf", "50 750 Td", "12 TL"]
        for line in page_lines:
            text_ops.append(f"({_pdf_escape(line)}) Tj")
            text_ops.append("T*")
        text_ops.append("ET")
        stream = "\n".join(text_ops)
        objects.append(f"<< /Length {len(stream.encode('utf-8'))} >>\nstream\n{stream}\nendstream")

    output = ["%PDF-1.4\n"]
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(sum(len(part.encode("utf-8")) for part in output))
        output.append(f"{index} 0 obj\n{obj}\nendobj\n")
    xref_offset = sum(len(part.encode("utf-8")) for part in output)
    output.append(f"xref\n0 {len(objects) + 1}\n")
    output.append("0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.append(f"{offset:010d} 00000 n \n")
    output.append(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n"
    )
    path.write_bytes("".join(output).encode("utf-8"))


def save_final_report(run: dict[str, Any]) -> dict[str, Path]:
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
        "target_modes": run.get("target_modes"),
        "guardrails_enabled": run.get("guardrails_enabled"),
        "selected_methods": run.get("selected_methods"),
        "selected_profile_ids": run.get("selected_profile_ids"),
        "profiles": run.get("profiles", []),
        "profile": run.get("profile"),
        "framework": run.get("framework"),
        "final_scores": run.get("final_scores"),
        "eb_comparison_examples": _eb_comparison_examples(run.get("cases", [])),
        "cases": run.get("cases", []),
    }
    path = json_report_path(run["run_id"])
    with NamedTemporaryFile("w", delete=False, dir=REPORTS_DIR, encoding="utf-8") as tmp:
        json.dump(report, tmp, indent=2, sort_keys=True)
        tmp_path = Path(tmp.name)
    tmp_path.replace(path)
    pdf_path = pdf_report_path(run["run_id"])
    _write_simple_pdf(pdf_path, _report_lines(report))
    return {"json": path, "pdf": pdf_path}
