"""Black-box runner that fires red-team prompts at the backend chat endpoint."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import random
import time
from typing import Any
from uuid import uuid4

import httpx

from .llm_grader import grade_case_with_llm
from .scoring import recompute_final_scores, score_case
from .storage import load_run, save_run
from .test_suites import METHOD_FRAMEWORK, METHOD_NAMES, build_test_prompts


DEFAULT_BACKEND_URL = "http://127.0.0.1:8000"
ALL_METHODS = tuple(METHOD_NAMES.keys())


def utc_now() -> str:
    """Return an ISO-8601 UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


def _clean_backend_url(url: str | None) -> str:
    return (url or DEFAULT_BACKEND_URL).strip().rstrip("/")


def _normalize_methods(selected_methods: list[str] | None) -> list[str]:
    methods = [method for method in (selected_methods or ALL_METHODS) if method in METHOD_NAMES]
    return methods or list(ALL_METHODS)


def _normalize_target_mode(target_mode: str | None) -> str:
    if target_mode == "lightweight_no_guardrails":
        return "lightweight_no_guardrails"
    return "guardrailed"


def create_run(
    *,
    backend_url: str | None = None,
    country: str = "netherlands",
    seed: int | None = None,
    selected_methods: list[str] | None = None,
    target_mode: str | None = None,
) -> dict[str, Any]:
    """Create an empty run payload."""
    run_id = f"rt-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{uuid4().hex[:8]}"
    methods = _normalize_methods(selected_methods)
    mode = _normalize_target_mode(target_mode)
    return {
        "run_id": run_id,
        "status": "created",
        "created_at": utc_now(),
        "completed_at": None,
        "backend_url": _clean_backend_url(backend_url),
        "country": country,
        "seed": seed,
        "target_mode": mode,
        "guardrails_enabled": mode != "lightweight_no_guardrails",
        "profile": None,
        "methods": METHOD_NAMES,
        "selected_methods": methods,
        "framework": {
            "source_alignment": [
                "manual static red-team prompt corpus",
                "single-turn black-box attacks against the deployed backend",
                "automated attack-success scoring",
                "human-in-the-loop adjudication for qualitative or borderline cases",
                "final method-level and overall quantitative scores",
            ],
            "method_framework": METHOD_FRAMEWORK,
            "prompts_per_method": 10,
            "selected_methods": methods,
            "target_mode": mode,
            "current_scope": "single-turn prompt and token attacks, boundary probes, framing probes, stylometric probes, and persuasion probes",
            "future_scope": "multi-turn and iterative adaptive attack generation can be added without changing the backend chat system",
        },
        "cancel_requested": False,
        "progress": {
            "total_cases": 0,
            "completed_cases": 0,
            "current_method": None,
            "current_method_name": None,
            "current_prompt_id": None,
            "current_message": None,
            "current_step": "created",
        },
        "cases": [],
        "errors": [],
        "final_scores": {
            "overall_score": 0.0,
            "method_scores": {},
            "pending_human_reviews": 0,
            "completed_human_reviews": 0,
            "is_final": False,
        },
    }


def _cancel_requested(run_id: str) -> bool:
    try:
        return bool(load_run(run_id).get("cancel_requested"))
    except FileNotFoundError:
        return False


def _mark_cancelled(run: dict[str, Any]) -> None:
    run["status"] = "cancelled"
    run["completed_at"] = utc_now()
    run["progress"]["current_step"] = "cancelled"
    run["final_scores"] = recompute_final_scores(run)
    save_run(run)


def _fetch_personas(*, client: httpx.Client, backend_url: str, country: str) -> list[dict[str, Any]]:
    response = client.get(
        f"{backend_url}/api/chat/personas",
        params={"country": country, "limit": 30},
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    return payload.get("personas", [])


def _parse_sse_response(response: httpx.Response) -> dict[str, Any]:
    """Parse the backend SSE stream into text and metadata events."""
    current_event = "message"
    response_parts: list[str] = []
    raw_events: list[dict[str, Any]] = []
    user_analysis = None
    response_analysis = None
    agent_state = None
    errors: list[str] = []
    last_response_event = None

    for raw_line in response.iter_lines():
        if not raw_line:
            current_event = "message"
            continue
        line = raw_line if isinstance(raw_line, str) else raw_line.decode("utf-8")
        if line.startswith("event: "):
            current_event = line[7:].strip()
            continue
        if not line.startswith("data: "):
            continue
        data = line[6:]
        if data == "[DONE]":
            break

        try:
            payload = json.loads(data)
        except json.JSONDecodeError:
            payload = {"text": data}

        raw_events.append({"event": current_event, "payload": payload})

        if current_event == "user_message_analysis":
            user_analysis = payload.get("analysis")
        elif current_event == "agent_state":
            agent_state = payload
        elif current_event == "message_part":
            response_parts.append(payload.get("text", ""))
            if payload.get("analysis") and response_analysis is None:
                response_analysis = payload.get("analysis")
            last_response_event = current_event
        elif current_event == "message":
            text = payload.get("text", "")
            if last_response_event == "message" and response_parts:
                response_parts[-1] += text
            else:
                response_parts.append(text)
            last_response_event = current_event
        elif current_event == "system":
            response_parts.append(payload.get("text", ""))
            last_response_event = current_event
        elif current_event == "error":
            text = payload.get("text", "")
            errors.append(text)
            response_parts.append(text)
            last_response_event = current_event

    return {
        "response_text": "\n\n".join(part for part in response_parts if part),
        "user_analysis": user_analysis,
        "response_analysis": response_analysis,
        "agent_state": agent_state,
        "events": raw_events,
        "errors": errors,
    }


def _call_chat(
    *,
    client: httpx.Client,
    backend_url: str,
    profile: dict[str, Any],
    message: str,
    session_id: str,
    disable_guardrails: bool,
) -> dict[str, Any]:
    with client.stream(
        "POST",
        f"{backend_url}/api/chat/chat_message",
        json={
            "message": message,
            "persona_details": profile["details"],
            "persona_country": profile["country"],
            "chat_history": [],
            "client_session_id": session_id,
            "disable_guardrails": disable_guardrails,
        },
        headers={"X-Red-Team-Mode": "true"} if disable_guardrails else None,
        timeout=180,
    ) as response:
        response.raise_for_status()
        return _parse_sse_response(response)


def execute_run(run: dict[str, Any]) -> None:
    """Execute all red-team prompts for a run, saving after every case."""
    run["status"] = "running"
    run["started_at"] = utc_now()
    save_run(run)

    randomizer = random.Random(run.get("seed"))
    tests = build_test_prompts(
        max_prompts_per_method=10,
        selected_methods=run.get("selected_methods"),
    )
    randomizer.shuffle(tests)
    session_id = f"red-team-{run['run_id']}"
    run["progress"].update(
        {
            "total_cases": len(tests),
            "completed_cases": 0,
            "current_step": "fetching random SSA profile",
        }
    )
    save_run(run)

    try:
        with httpx.Client() as client:
            personas = _fetch_personas(
                client=client,
                backend_url=run["backend_url"],
                country=run["country"],
            )
            if not personas:
                raise RuntimeError("No personas returned by backend.")
            profile = randomizer.choice(personas)
            run["profile"] = {
                "id": profile.get("id"),
                "label": profile.get("label"),
                "country": profile.get("country"),
                "index": profile.get("index"),
                "traits": profile.get("traits", {}),
            }
            save_run(run)

            for case_index, test in enumerate(tests, start=1):
                if _cancel_requested(run["run_id"]):
                    _mark_cancelled(run)
                    return

                run["progress"].update(
                    {
                        "completed_cases": case_index - 1,
                        "current_method": test.method,
                        "current_method_name": METHOD_NAMES[test.method],
                        "current_prompt_id": test.prompt_id,
                        "current_message": test.message,
                        "current_step": "executing prompt against backend chat endpoint",
                    }
                )
                save_run(run)

                started = time.time()
                case: dict[str, Any] = {
                    "case_id": f"{run['run_id']}-{test.prompt_id}",
                    "method": test.method,
                    "method_name": METHOD_NAMES[test.method],
                    "prompt_id": test.prompt_id,
                    "message": test.message,
                    "expectation": test.expectation,
                    "expected_answer": test.expected_answer,
                    "attack_family": test.attack_family,
                    "interaction_mode": test.interaction_mode,
                    "target_guardrail": test.target_guardrail,
                    "evaluation_mode": test.evaluation_mode,
                    "target_mode": run.get("target_mode", "guardrailed"),
                    "guardrails_enabled": run.get("guardrails_enabled", True),
                    "expected_human_review": test.requires_human_review,
                    "started_at": utc_now(),
                    "completed_at": None,
                    "duration_seconds": None,
                    "status": "running",
                    "response_text": "",
                    "user_analysis": None,
                    "response_analysis": None,
                    "agent_state": None,
                    "errors": [],
                }
                run["cases"].append(case)
                save_run(run)

                try:
                    run["progress"]["current_step"] = "waiting for backend response and guardrail analysis"
                    save_run(run)
                    result = _call_chat(
                        client=client,
                        backend_url=run["backend_url"],
                        profile=profile,
                        message=test.message,
                        session_id=session_id,
                        disable_guardrails=not run.get("guardrails_enabled", True),
                    )
                    case.update(result)
                    run["progress"]["current_step"] = "grading prompt and response with LLM evaluator"
                    save_run(run)
                    case["llm_grade"] = grade_case_with_llm(case, profile)
                    case.update(score_case(case))
                    case["status"] = "completed"
                except Exception as exc:
                    case["status"] = "error"
                    case["errors"] = [f"{type(exc).__name__}: {exc}"]
                    case["automated_score"] = 0.0
                    case["needs_human_review"] = True
                    case["automated_reasons"] = ["case execution failed"]

                if _cancel_requested(run["run_id"]):
                    run["cancel_requested"] = True
                case["completed_at"] = utc_now()
                case["duration_seconds"] = round(time.time() - started, 3)
                run["progress"].update(
                    {
                        "completed_cases": case_index,
                        "current_step": "scoring automated result",
                    }
                )
                run["final_scores"] = recompute_final_scores(run)
                save_run(run)
                if run.get("cancel_requested"):
                    _mark_cancelled(run)
                    return

        run["status"] = "completed"
        run["completed_at"] = utc_now()
        run["progress"].update(
            {
                "completed_cases": len(tests),
                "current_method": None,
                "current_method_name": None,
                "current_prompt_id": None,
                "current_message": None,
                "current_step": "completed; awaiting human mediation where required",
            }
        )
        run["final_scores"] = recompute_final_scores(run)
        save_run(run)
    except Exception as exc:
        run["status"] = "error"
        run["errors"].append(f"{type(exc).__name__}: {exc}")
        run["completed_at"] = utc_now()
        run["progress"]["current_step"] = "error"
        run["final_scores"] = recompute_final_scores(run)
        save_run(run)
