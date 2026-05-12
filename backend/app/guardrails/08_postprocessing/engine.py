"""Post-generation subjective framing and persuasive governance."""

from dataclasses import dataclass, field
import re

from app.guardrails.schemas import GuardrailInput, GuardrailSignals, PolicyDecision
from app.utils import build_chat_messages, create_system_prompt, run_chat_completion
from .constants import (
    HIGH_STAKES_ADVICE_MARKERS,
    LIMITED_EXPERTISE_MARKERS,
    LOW_STAKES_ADVICE_MARKERS,
    OBJECTIVE_MARKERS,
    PERSUASIVE_MARKERS,
    SENSITIVE_TOPICS,
    SUBJECTIVE_MARKERS,
)
from .prompts import POSTPROCESSING_CORRECTOR_SYS_PROMPT, build_correction_prompt


@dataclass(slots=True)
class PostprocessResult:
    """Result of response validation and optional correction."""

    final_response: str
    changed: bool = False
    reasons: list[str] = field(default_factory=list)
    subjectivity_score: float = 0.0
    objectivity_score: float = 0.0
    persuasion_score: float = 0.0


def _sentences(text: str) -> list[str]:
    """Split text into rough sentences without external NLP dependencies."""
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]


def _marker_score(text: str, markers: tuple[str, ...]) -> float:
    """Return a compact marker score."""
    normalized = text.lower()
    matches = sum(1 for marker in markers if marker in normalized)
    return min(1.0, round(matches / 3, 3))


def _subjectivity_scores(text: str) -> tuple[float, float]:
    """Approximate sentence-level subjective/objective balance."""
    sentence_list = _sentences(text)
    if not sentence_list:
        return 0.0, 0.0

    subjective_hits = 0
    objective_hits = 0
    for sentence in sentence_list:
        normalized = sentence.lower()
        if any(marker in normalized for marker in SUBJECTIVE_MARKERS):
            subjective_hits += 1
        if any(marker in normalized for marker in OBJECTIVE_MARKERS):
            objective_hits += 1

    subjectivity = subjective_hits / len(sentence_list)
    objectivity = max(objective_hits / len(sentence_list), _marker_score(text, OBJECTIVE_MARKERS))
    return round(subjectivity, 3), round(objectivity, 3)


def _persuasion_score(text: str) -> float:
    """Approximate persuasive pressure in the generated response."""
    return _marker_score(text, PERSUASIVE_MARKERS)


def _topic_is_sensitive(user_message: str) -> bool:
    """Return True when persuasion should be especially restrained."""
    normalized = user_message.lower()
    return any(topic in normalized for topic in SENSITIVE_TOPICS)


def _is_low_stakes_personal_advice(user_message: str) -> bool:
    """Return True for everyday advice where expert disclaimers sound unnatural."""
    normalized = user_message.lower()
    return (
        any(marker in normalized for marker in LOW_STAKES_ADVICE_MARKERS)
        and not any(marker in normalized for marker in HIGH_STAKES_ADVICE_MARKERS)
    )


def _limited_expertise_count(text: str) -> int:
    """Count repeated limited-expertise disclaimers in a response."""
    normalized = text.lower()
    return sum(normalized.count(marker) for marker in LIMITED_EXPERTISE_MARKERS)


def _needs_disclaimer_correction(*, user_message: str, response: str) -> bool:
    """Return True when expertise disclaimers are repetitive or unnecessary."""
    disclaimer_count = _limited_expertise_count(response)
    if disclaimer_count > 1:
        return True
    return disclaimer_count == 1 and _is_low_stakes_personal_advice(user_message)


def _needs_subjectivity_correction(*, policy: PolicyDecision, subjectivity: float, objectivity: float) -> bool:
    """Return True when a subjective-mode answer sounds too factual or authoritative."""
    return (
        policy.response_mode != "limited_factual"
        and policy.authority_level != "high"
        and objectivity >= 0.34
        and subjectivity < 0.34
    )


def _needs_persuasion_correction(*, user_message: str, policy: PolicyDecision, persuasion: float) -> bool:
    """Return True when persuasive pressure exceeds the framework boundaries."""
    if persuasion >= 0.67:
        return True
    return persuasion >= 0.34 and (
        _topic_is_sensitive(user_message)
        or policy.relevance_score < 0.7
        or policy.action in {"limited_answer", "redirect"}
    )


def apply_postprocessing(
    *,
    response: str,
    guardrail_input: GuardrailInput,
    signals: GuardrailSignals,
    policy: PolicyDecision,
) -> PostprocessResult:
    """Validate response subjectivity and persuasion, regenerating when needed."""
    subjectivity, objectivity = _subjectivity_scores(response)
    persuasion = _persuasion_score(response)
    reasons: list[str] = []

    if _needs_subjectivity_correction(
        policy=policy,
        subjectivity=subjectivity,
        objectivity=objectivity,
    ):
        reasons.append("response is too factual or authoritative for subjective mode")

    if _needs_persuasion_correction(
        user_message=guardrail_input.user_message,
        policy=policy,
        persuasion=persuasion,
    ):
        reasons.append("response exceeds acceptable persuasive intensity")

    if _needs_disclaimer_correction(
        user_message=guardrail_input.user_message,
        response=response,
    ):
        reasons.append("response repeats or unnecessarily uses limited-expertise disclaimers")

    if not reasons:
        return PostprocessResult(
            final_response=response,
            subjectivity_score=subjectivity,
            objectivity_score=objectivity,
            persuasion_score=persuasion,
        )

    system_prompt = create_system_prompt(
        POSTPROCESSING_CORRECTOR_SYS_PROMPT,
        guardrail_input.persona_biography,
    )
    correction_prompt = build_correction_prompt(
        response=response,
        policy=policy,
        reasons=reasons,
    )
    corrected = run_chat_completion(
        messages=build_chat_messages(
            system_prompt=system_prompt,
            user_message=correction_prompt,
            chat_history=[],
        ),
        temperature=0.25,
    ).strip()

    corrected_subjectivity, corrected_objectivity = _subjectivity_scores(corrected)
    corrected_persuasion = _persuasion_score(corrected)
    return PostprocessResult(
        final_response=corrected or response,
        changed=bool(corrected),
        reasons=reasons,
        subjectivity_score=corrected_subjectivity,
        objectivity_score=corrected_objectivity,
        persuasion_score=corrected_persuasion,
    )
