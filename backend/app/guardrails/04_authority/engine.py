"""Pre-generation subjective framing and authority modulation."""

from app.guardrails.schemas import AuthoritySignal
from .constants import (
    FACTUALITY_LEVEL_DESCRIPTIONS,
    FACTUAL_INTENT_MARKERS,
    SUBJECTIVE_INTENT_MARKERS,
)
from .prompts import build_authority_judge_prompt


def _score_markers(message: str, markers: tuple[str, ...]) -> float:
    """Score marker matches on a compact 0-1 scale."""
    normalized = message.lower()
    matches = sum(1 for marker in markers if marker in normalized)
    return min(1.0, round(matches / 3, 3))


def _select_factuality_level(*, factual_score: float, subjective_score: float) -> tuple[str, str, str]:
    """Select the requested factuality/subjectivity level from intent scores."""
    if factual_score >= 0.67 and factual_score > subjective_score:
        factuality_level = "limited_factual"
        authority_level = "medium"
        instruction = (
            "The user strongly appears to ask for factual clarification. Treat this only as requested "
            "factuality; the judge must lower it if the persona lacks topic knowledge or relevance."
        )
    elif factual_score >= 0.34 and factual_score > subjective_score:
        factuality_level = "uncertain_interpretation"
        authority_level = "low"
        instruction = (
            "The user appears to ask for explanation or clarification, but not enough to justify strong "
            "factual authority. Prefer cautious interpretation unless the judge finds strong epistemic fit."
        )
    elif subjective_score >= 0.67 and subjective_score > factual_score:
        factuality_level = "belief_affirmation"
        authority_level = "low"
        instruction = (
            "The user strongly invites belief, preference, concern, or personal perspective. Use belief- "
            "or value-oriented framing rather than factual authority."
        )
    elif subjective_score >= 0.34 and subjective_score >= factual_score:
        factuality_level = "anecdotal"
        authority_level = "low"
        instruction = (
            "The user invites personal interpretation or lived experience. Prefer anecdotal, first-person "
            "framing with only light factual support."
        )
    else:
        factuality_level = "subjective"
        authority_level = "low"
        instruction = (
            "No strong factual-verification request was detected. Use the default SSA stance: subjective, "
            "persona-grounded, and based on lived experience, belief, or cautious interpretation."
        )

    return factuality_level, authority_level, instruction


def evaluate_authority_modulation(*, user_message: str) -> AuthoritySignal:
    """Select the intended factual/subjective stance before generation."""
    factual_score = _score_markers(user_message, FACTUAL_INTENT_MARKERS)
    subjective_score = _score_markers(user_message, SUBJECTIVE_INTENT_MARKERS)
    factuality_level, authority_level, instruction = _select_factuality_level(
        factual_score=factual_score,
        subjective_score=subjective_score,
    )
    response_mode = factuality_level

    judge_prompt = build_authority_judge_prompt(
        response_mode=response_mode,
        factuality_level=factuality_level,
        factuality_description=FACTUALITY_LEVEL_DESCRIPTIONS[factuality_level],
        factual_score=factual_score,
        subjective_score=subjective_score,
        authority_level=authority_level,
        instruction=instruction,
    )

    return AuthoritySignal(
        response_mode=response_mode,
        factuality_level=factuality_level,
        factual_intent_score=factual_score,
        subjective_intent_score=subjective_score,
        authority_level=authority_level,
        summary=instruction,
        judge_prompt=judge_prompt,
    )
