"""LLM-based policy selection for the guardrailed response pipeline."""

import json

from app.guardrails.schemas import GuardrailInput, GuardrailSignals, PolicyDecision
from app.guardrails.session_trace import append_kv_block, append_named_block
from app.logging import get_logger
from app.utils import build_chat_messages, run_chat_completion
from .prompts import GUARDRAILED_JUDGE_SYS_PROMPT, build_judge_user_message


log = get_logger(__name__)


def _safe_float(value, fallback: float) -> float:
    """Convert JSON numeric fields safely into floats."""
    try:
        return round(float(value), 3)
    except (TypeError, ValueError):
        return fallback


def _normalize_action(action: str | None) -> str:
    """Normalize the judge action into a supported policy action."""
    if action in {"allow", "limited_answer", "redirect", "refuse"}:
        return action
    return "limited_answer"


def _normalize_expertise_basis(value: str | None) -> str:
    """Normalize the expertise basis into a supported category."""
    if value in {
        "none",
        "biography_interest",
        "lived_experience",
        "work_exposure",
        "education_background",
        "domain_expert",
    }:
        return value
    return "none"


def _normalize_hedging_style(value: str | None) -> str:
    """Normalize hedging style into a supported category."""
    if value in {"low", "medium", "high"}:
        return value
    return "medium"


def _normalize_confidence_style(value: str | None) -> str:
    """Normalize confidence style into a supported category."""
    if value in {"tentative", "balanced", "assured"}:
        return value
    return "balanced"


def _normalize_response_length_target(value: str | None) -> str:
    """Normalize response length target into a supported category."""
    if value in {"very_short", "short", "medium", "long"}:
        return value
    return "short"


def _normalize_response_mode(value: str | None, fallback: str) -> str:
    """Normalize authority response mode into a supported category."""
    if value in {
        "subjective",
        "anecdotal",
        "belief_affirmation",
        "uncertain_interpretation",
        "limited_factual",
    }:
        return value
    return fallback


def _normalize_factuality_level(value: str | None, fallback: str) -> str:
    """Normalize factuality level into the supported five-point scale."""
    if value in {
        "belief_affirmation",
        "anecdotal",
        "subjective",
        "uncertain_interpretation",
        "limited_factual",
    }:
        return value
    return fallback


def _normalize_authority_level(value: str | None, fallback: str) -> str:
    """Normalize authority level into a supported category."""
    if value in {"low", "medium", "high"}:
        return value
    return fallback


def _safe_bool(value, fallback: bool) -> bool:
    """Convert JSON boolean-like fields safely into bools."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "yes", "1"}:
            return True
        if normalized in {"false", "no", "0"}:
            return False
    return fallback


def _looks_like_policy_payload(payload: object) -> bool:
    """Return True when the payload already looks like the expected judge JSON."""
    return isinstance(payload, dict) and (
        "action" in payload
        or "response_guidance" in payload
        or "rationale" in payload
    )


def _unwrap_policy_payload(payload: object) -> dict | None:
    """Recover the real policy payload from common wrapper shapes returned by the judge."""
    current = payload

    for _ in range(4):
        if _looks_like_policy_payload(current):
            return current

        if isinstance(current, dict):
            for key in ("final", "response", "output", "result", "content"):
                nested = current.get(key)
                if _looks_like_policy_payload(nested):
                    return nested
                if isinstance(nested, str):
                    try:
                        current = json.loads(nested)
                        break
                    except json.JSONDecodeError:
                        continue
                if isinstance(nested, dict):
                    current = nested
                    break
            else:
                return None
            continue

        if isinstance(current, str):
            try:
                current = json.loads(current)
            except json.JSONDecodeError:
                return None
            continue

        return None

    if _looks_like_policy_payload(current):
        return current
    return None


def _parse_judge_response(raw_response: str, signals: GuardrailSignals) -> PolicyDecision:
    """Parse the judge JSON response with a safe fallback."""
    try:
        decoded = json.loads(raw_response)
    except json.JSONDecodeError:
        log.info("Judge parsing fallback")
        log.info("  Reason: invalid JSON returned by judge model")
        return PolicyDecision(
            action="limited_answer",
            rationale="The judge response could not be parsed cleanly, so the system falls back to a cautious answer.",
            response_guidance="Answer gently and cautiously from the persona's perspective. Stay grounded in the biography, keep the language plain, and avoid overclaiming.",
            response_length_target="short",
            detail_allowed=False,
            expertise_basis="none",
            hedging_style="medium",
            confidence_style="balanced",
            register_style="everyday",
            sentence_style="mixed",
            abstraction_level="mixed",
            vocabulary_level="moderate",
            explanation_style="balanced",
            response_mode=signals.authority.response_mode,
            factuality_level=signals.authority.factuality_level,
            authority_level=signals.authority.authority_level,
            lexical_score=1.0 if signals.lexical.triggered else 0.0,
            relevance_score=0.5,
            epistemic_score=0.5,
            knowledge_level="limited",
            language_level="plain",
            tone_style="cautious",
            emotional_style="neutral",
        )

    payload = _unwrap_policy_payload(decoded)
    if payload is None:
        log.info("Judge parsing fallback")
        log.info("  Reason: valid JSON returned, but no policy payload could be unwrapped")
        return PolicyDecision(
            action="limited_answer",
            rationale="The judge response used an unexpected structure, so the system falls back to a cautious answer.",
            response_guidance="Answer gently and cautiously from the persona's perspective. Stay grounded in the biography, keep the language plain, and avoid overclaiming.",
            response_length_target="short",
            detail_allowed=False,
            expertise_basis="none",
            hedging_style="medium",
            confidence_style="balanced",
            register_style="everyday",
            sentence_style="mixed",
            abstraction_level="mixed",
            vocabulary_level="moderate",
            explanation_style="balanced",
            response_mode=signals.authority.response_mode,
            factuality_level=signals.authority.factuality_level,
            authority_level=signals.authority.authority_level,
            lexical_score=1.0 if signals.lexical.triggered else 0.0,
            relevance_score=0.5,
            epistemic_score=0.5,
            knowledge_level="limited",
            language_level="plain",
            tone_style="cautious",
            emotional_style="neutral",
        )

    return PolicyDecision(
        action=_normalize_action(payload.get("action")),
        rationale=payload.get("rationale", "No rationale returned by judge."),
        response_guidance=payload.get(
            "response_guidance",
            "Answer cautiously from the persona's perspective and stay grounded in the biography.",
        ),
        response_length_target=_normalize_response_length_target(payload.get("response_length_target")),
        detail_allowed=_safe_bool(payload.get("detail_allowed"), False),
        expertise_basis=_normalize_expertise_basis(payload.get("expertise_basis")),
        hedging_style=_normalize_hedging_style(payload.get("hedging_style")),
        confidence_style=_normalize_confidence_style(payload.get("confidence_style")),
        register_style=payload.get("register_style", "everyday"),
        sentence_style=payload.get("sentence_style", "mixed"),
        abstraction_level=payload.get("abstraction_level", "mixed"),
        vocabulary_level=payload.get("vocabulary_level", "moderate"),
        explanation_style=payload.get("explanation_style", "balanced"),
        response_mode=_normalize_response_mode(
            payload.get("response_mode"),
            signals.authority.response_mode,
        ),
        factuality_level=_normalize_factuality_level(
            payload.get("factuality_level"),
            signals.authority.factuality_level,
        ),
        authority_level=_normalize_authority_level(
            payload.get("authority_level"),
            signals.authority.authority_level,
        ),
        lexical_score=_safe_float(payload.get("lexical_score"), 1.0 if signals.lexical.triggered else 0.0),
        relevance_score=_safe_float(payload.get("relevance_score"), 0.5),
        epistemic_score=_safe_float(payload.get("epistemic_score"), 0.5),
        knowledge_level=payload.get("knowledge_level", "limited"),
        language_level=payload.get("language_level", "plain"),
        tone_style=payload.get("tone_style", "cautious"),
        emotional_style=payload.get("emotional_style", "neutral"),
    )


# =============================================================================
# Public Decision Entry Point
# =============================================================================

def decide_policy(*, guardrail_input: GuardrailInput, signals: GuardrailSignals) -> PolicyDecision:
    """Convert guardrail signals into LLM-judged response advice."""
    judge_user_message = build_judge_user_message(
        guardrail_input=guardrail_input,
        signals=signals,
    )
    messages = build_chat_messages(
        system_prompt=GUARDRAILED_JUDGE_SYS_PROMPT,
        user_message=judge_user_message,
        chat_history=guardrail_input.chat_history,
    )
    append_named_block(
        trace=guardrail_input.session_trace,
        title="Judge System Prompt",
        content=GUARDRAILED_JUDGE_SYS_PROMPT,
        step_label="LAYER 06",
    )
    append_named_block(
        trace=guardrail_input.session_trace,
        title="Judge User Prompt",
        content=judge_user_message,
        step_label="LAYER 06",
    )
    append_named_block(
        trace=guardrail_input.session_trace,
        title="Judge Messages Payload",
        content=messages,
        step_label="LAYER 06",
    )

    raw_response = run_chat_completion(
        messages=messages,
        temperature=0.1,
        json_mode=True,
    )
    append_named_block(
        trace=guardrail_input.session_trace,
        title="Judge Raw Response",
        content=raw_response,
        step_label="LAYER 06",
    )
    decision = _parse_judge_response(raw_response, signals)

    log.info(
        "Layer 06 parsed policy: %s action, %.2f relevance, %.2f epistemic, %s factuality.",
        decision.action,
        decision.relevance_score,
        decision.epistemic_score,
        decision.factuality_level,
    )
    append_kv_block(
        trace=guardrail_input.session_trace,
        title="Judge Policy Decision",
        step_label="LAYER 06",
        items=[
            ("Action", decision.action),
            ("Lexical score", decision.lexical_score),
            ("Relevance score", decision.relevance_score),
            ("Epistemic score", decision.epistemic_score),
            ("Knowledge level", decision.knowledge_level),
            ("Response length target", decision.response_length_target),
            ("Detail allowed", decision.detail_allowed),
            ("Expertise basis", decision.expertise_basis),
            ("Hedging style", decision.hedging_style),
            ("Confidence style", decision.confidence_style),
            ("Language level", decision.language_level),
            ("Register style", decision.register_style),
            ("Sentence style", decision.sentence_style),
            ("Abstraction level", decision.abstraction_level),
            ("Vocabulary level", decision.vocabulary_level),
            ("Explanation style", decision.explanation_style),
            ("Response mode", decision.response_mode),
            ("Factuality level", decision.factuality_level),
            ("Authority level", decision.authority_level),
            ("Tone style", decision.tone_style),
            ("Emotional style", decision.emotional_style),
            ("Rationale", decision.rationale),
            ("Response guidance", decision.response_guidance),
        ],
    )

    return decision
