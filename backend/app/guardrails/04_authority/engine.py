"""Pre-generation subjective framing and authority modulation."""

from app.guardrails.schemas import AuthoritySignal
from .constants import (
    FACTUAL_INTENT_MARKERS,
    SUBJECTIVE_INTENT_MARKERS,
)
from .prompts import build_authority_judge_prompt


def _score_markers(message: str, markers: tuple[str, ...]) -> float:
    """Score marker matches on a compact 0-1 scale."""
    normalized = message.lower()
    matches = sum(1 for marker in markers if marker in normalized)
    return min(1.0, round(matches / 3, 3))


def evaluate_authority_modulation(*, user_message: str) -> AuthoritySignal:
    """Select the intended factual/subjective stance before generation."""
    factual_score = _score_markers(user_message, FACTUAL_INTENT_MARKERS)
    subjective_score = _score_markers(user_message, SUBJECTIVE_INTENT_MARKERS)

    if factual_score >= 0.34 and factual_score > subjective_score:
        response_mode = "limited_factual"
        authority_level = "medium"
        instruction = (
            "The user appears to ask for factual clarification. Allow concise factual framing, "
            "but keep it within the persona's realistic knowledge scope and avoid expert authority."
        )
    elif subjective_score >= 0.34:
        response_mode = "subjective"
        authority_level = "low"
        instruction = (
            "The user appears to invite personal interpretation. Prefer first-person, "
            "persona-grounded framing over objective assistant-like claims."
        )
    else:
        response_mode = "subjective"
        authority_level = "low"
        instruction = (
            "No clear factual-verification request was detected. Use the default SSA stance: "
            "subjective, persona-grounded, and based on lived experience or belief."
        )

    judge_prompt = build_authority_judge_prompt(
        response_mode=response_mode,
        factual_score=factual_score,
        subjective_score=subjective_score,
        authority_level=authority_level,
        instruction=instruction,
    )

    return AuthoritySignal(
        response_mode=response_mode,
        factual_intent_score=factual_score,
        subjective_intent_score=subjective_score,
        authority_level=authority_level,
        summary=instruction,
        judge_prompt=judge_prompt,
    )
