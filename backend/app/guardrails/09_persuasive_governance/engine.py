"""Post-generation persuasive governance validation."""

from dataclasses import dataclass, field
from functools import lru_cache
import importlib.util
import re

from app.guardrails.schemas import GuardrailInput, GuardrailSignals, PolicyDecision
from app.utils import build_chat_messages, create_system_prompt, run_chat_completion
from .constants import (
    PERSUASION_MODEL_ID,
    PERSUASION_PIPELINE_TASK,
    PERSUASION_TOKENIZER_ID,
    PERSUASIVE_MARKERS,
    SENSITIVE_TOPICS,
)
from .prompts import (
    PERSUASIVE_GOVERNANCE_CORRECTOR_SYS_PROMPT,
    build_persuasive_governance_correction_prompt,
)


@dataclass(slots=True)
class PersuasiveGovernanceResult:
    """Result of persuasive governance validation."""

    final_response: str
    changed: bool = False
    reasons: list[str] = field(default_factory=list)
    persuasion_score: float = 0.0
    persuasive_sentences: list[str] = field(default_factory=list)
    detector_source: str = "heuristic_fallback"


def _sentences(text: str) -> list[str]:
    """Split text into rough sentences without external NLP dependencies."""
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]


def _marker_score(text: str, markers: tuple[str, ...]) -> float:
    """Return a compact marker score."""
    normalized = text.lower()
    matches = sum(1 for marker in markers if marker in normalized)
    return min(1.0, round(matches / 3, 3))


@lru_cache(maxsize=1)
def _persuasion_pipeline():
    """Load chreh/persuasive_language_detector when transformers is installed."""
    if importlib.util.find_spec("transformers") is None:
        return None

    try:
        from transformers import pipeline
    except ImportError:
        return None

    try:
        return pipeline(
            task=PERSUASION_PIPELINE_TASK,
            model=PERSUASION_MODEL_ID,
            tokenizer=PERSUASION_TOKENIZER_ID,
            truncation=True,
        )
    except Exception:
        return None


def _persuasive_label_score(classification) -> float:
    """Extract a persuasion probability from a transformers classification result."""
    if isinstance(classification, list):
        if classification and isinstance(classification[0], list):
            classification = classification[0]
        if classification and isinstance(classification[0], dict):
            scores = [
                item.get("score", 0.0)
                for item in classification
                if _label_is_persuasive(str(item.get("label", "")))
            ]
            if scores:
                return max(scores)
            return max((item.get("score", 0.0) for item in classification), default=0.0)

    if isinstance(classification, dict):
        label = str(classification.get("label", ""))
        normalized_label = label.lower().replace("-", "_").replace(" ", "_")
        score = float(classification.get("score", 0.0))
        if _label_is_persuasive(label):
            return score
        if normalized_label in {"label_0", "non_persuasive", "not_persuasive"}:
            return 1.0 - score
        return score

    return 0.0


def _label_is_persuasive(label: str) -> bool:
    """Return True for persuasive labels in model outputs."""
    normalized = label.lower().replace("-", "_").replace(" ", "_")
    return normalized in {"label_1", "persuasive", "is_persuasive"} or (
        "persuasive" in normalized and "non" not in normalized and "not" not in normalized
    )


def _package_persuasion_analysis(text: str) -> tuple[float, list[str]] | None:
    """Run chreh/persuasive_language_detector when the local model stack is available."""
    classifier = _persuasion_pipeline()
    if classifier is None:
        return None

    sentence_list = _sentences(text)
    if not sentence_list:
        return 0.0, []

    scores: list[float] = []
    persuasive_sentences: list[str] = []
    for sentence in sentence_list:
        try:
            score = _persuasive_label_score(classifier(sentence))
        except Exception:
            return None

        score = round(float(score), 3)
        scores.append(score)
        if score >= 0.5:
            persuasive_sentences.append(sentence)

    return max(scores, default=0.0), persuasive_sentences


def _heuristic_persuasion_analysis(text: str) -> tuple[float, list[str]]:
    """Approximate persuasive pressure when the transformer model is unavailable."""
    persuasive_sentences = [
        sentence
        for sentence in _sentences(text)
        if any(marker in sentence.lower() for marker in PERSUASIVE_MARKERS)
    ]
    return _marker_score(text, PERSUASIVE_MARKERS), persuasive_sentences


def _persuasion_analysis(text: str) -> tuple[float, list[str], str]:
    """Return persuasive pressure from the package or fallback markers."""
    package_result = _package_persuasion_analysis(text)
    if package_result is not None:
        score, persuasive_sentences = package_result
        return round(score, 3), persuasive_sentences, "persuasive_language_detector"

    score, persuasive_sentences = _heuristic_persuasion_analysis(text)
    return score, persuasive_sentences, "heuristic_fallback"


def _topic_is_sensitive(user_message: str) -> bool:
    """Return True when persuasion should be especially restrained."""
    normalized = user_message.lower()
    return any(topic in normalized for topic in SENSITIVE_TOPICS)


def _needs_persuasion_correction(*, user_message: str, policy: PolicyDecision, persuasion: float) -> bool:
    """Return True when persuasive pressure exceeds the framework boundaries."""
    if persuasion >= 0.67:
        return True
    return persuasion >= 0.34 and (
        _topic_is_sensitive(user_message)
        or policy.relevance_score < 0.7
        or policy.action in {"limited_answer", "redirect"}
    )


def apply_persuasive_governance(
    *,
    response: str,
    guardrail_input: GuardrailInput,
    signals: GuardrailSignals,
    policy: PolicyDecision,
) -> PersuasiveGovernanceResult:
    """Validate persuasive pressure and regenerate when influence is too strong."""
    del signals
    persuasion, persuasive_sentences, detector_source = _persuasion_analysis(response)
    reasons: list[str] = []

    if _needs_persuasion_correction(
        user_message=guardrail_input.user_message,
        policy=policy,
        persuasion=persuasion,
    ):
        reasons.append("response exceeds acceptable persuasive intensity")

    if not reasons:
        return PersuasiveGovernanceResult(
            final_response=response,
            persuasion_score=persuasion,
            persuasive_sentences=persuasive_sentences,
            detector_source=detector_source,
        )

    system_prompt = create_system_prompt(
        PERSUASIVE_GOVERNANCE_CORRECTOR_SYS_PROMPT,
        guardrail_input.persona_biography,
    )
    correction_prompt = build_persuasive_governance_correction_prompt(
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

    corrected_persuasion, corrected_persuasive_sentences, corrected_detector_source = (
        _persuasion_analysis(corrected or response)
    )
    return PersuasiveGovernanceResult(
        final_response=corrected or response,
        changed=bool(corrected),
        reasons=reasons,
        persuasion_score=corrected_persuasion,
        persuasive_sentences=corrected_persuasive_sentences,
        detector_source=corrected_detector_source,
    )
