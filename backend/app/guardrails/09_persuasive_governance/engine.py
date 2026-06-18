"""Post-generation persuasive governance validation."""

from dataclasses import dataclass, field
from functools import lru_cache
import importlib.util
import logging
import re

from app.guardrails.topic_policy import get_topic_persuasion_threshold, normalize_topic_policy_category
from app.guardrails.schemas import GuardrailInput, GuardrailSignals, PolicyDecision
from app.utils import build_chat_messages, create_system_prompt, run_chat_completion
from .constants import (
    PERSUASION_MODEL_ID,
    PERSUASION_PIPELINE_TASK,
    PERSUASION_TOKENIZER_ID,
    PERSUASIVE_MARKERS,
)
from .prompts import (
    PERSUASIVE_GOVERNANCE_CORRECTOR_SYS_PROMPT,
    build_persuasive_governance_correction_prompt,
)


log = logging.getLogger(__name__)


@dataclass(slots=True)
class PersuasiveGovernanceResult:
    """Result of persuasive governance validation."""

    final_response: str
    changed: bool = False
    reasons: list[str] = field(default_factory=list)
    persuasion_score: float = 0.0
    persuasive_sentences: list[str] = field(default_factory=list)
    detector_source: str = "heuristic_fallback"
    persuasion_threshold: float = 0.5
    base_topic_threshold: float = 0.5
    topic_policy_category: str = "everyday_conversation"
    threshold_adjustments: list[str] = field(default_factory=list)
    sentence_scores: list[dict] = field(default_factory=list)
    threshold_check: dict = field(default_factory=dict)


@dataclass(slots=True)
class PersuasionAnalysis:
    """Detector output normalized for Layer 09 policy checks."""

    score: float = 0.0
    persuasive_sentences: list[str] = field(default_factory=list)
    detector_source: str = "heuristic_fallback"
    sentence_scores: list[dict] = field(default_factory=list)


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
        from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline
    except ImportError:
        return None

    try:
        tokenizer = AutoTokenizer.from_pretrained(PERSUASION_TOKENIZER_ID, local_files_only=True)
        model = AutoModelForSequenceClassification.from_pretrained(
            PERSUASION_MODEL_ID,
            local_files_only=True,
        )
    except Exception:
        try:
            tokenizer = AutoTokenizer.from_pretrained(PERSUASION_TOKENIZER_ID)
            model = AutoModelForSequenceClassification.from_pretrained(PERSUASION_MODEL_ID)
        except Exception:
            return None

    try:
        return pipeline(
            task=PERSUASION_PIPELINE_TASK,
            model=model,
            tokenizer=tokenizer,
            truncation=True,
            top_k=None,
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


def _package_persuasion_analysis(text: str) -> PersuasionAnalysis | None:
    """Run chreh/persuasive_language_detector when the local model stack is available."""
    classifier = _persuasion_pipeline()
    if classifier is None:
        return None

    sentence_list = _sentences(text)
    if not sentence_list:
        return PersuasionAnalysis(detector_source="persuasive_language_detector")

    scores: list[float] = []
    persuasive_sentences: list[str] = []
    sentence_scores: list[dict] = []
    for sentence in sentence_list:
        try:
            classification = classifier(sentence)
            score = _persuasive_label_score(classification)
        except Exception:
            return None

        score = round(float(score), 3)
        scores.append(score)
        sentence_scores.append(
            {
                "sentence": sentence,
                "persuasion_score": score,
                "raw_classification": classification,
            }
        )
        if score >= 0.5:
            persuasive_sentences.append(sentence)

    return PersuasionAnalysis(
        score=max(scores, default=0.0),
        persuasive_sentences=persuasive_sentences,
        detector_source="persuasive_language_detector",
        sentence_scores=sentence_scores,
    )


def _heuristic_persuasion_analysis(text: str) -> PersuasionAnalysis:
    """Approximate persuasive pressure when the transformer model is unavailable."""
    persuasive_sentences = [
        sentence
        for sentence in _sentences(text)
        if any(marker in sentence.lower() for marker in PERSUASIVE_MARKERS)
    ]
    return PersuasionAnalysis(
        score=_marker_score(text, PERSUASIVE_MARKERS),
        persuasive_sentences=persuasive_sentences,
        detector_source="heuristic_fallback",
        sentence_scores=[
            {
                "sentence": sentence,
                "persuasive_marker_match": sentence in persuasive_sentences,
            }
            for sentence in _sentences(text)
        ],
    )


def _persuasion_analysis(text: str) -> PersuasionAnalysis:
    """Return persuasive pressure from the package or fallback markers."""
    package_result = _package_persuasion_analysis(text)
    if package_result is not None:
        package_result.score = round(package_result.score, 3)
        return package_result

    return _heuristic_persuasion_analysis(text)


def warm_persuasion_detector() -> bool:
    """Warm the Hugging Face persuasion detector outside the request path."""
    analysis = _package_persuasion_analysis("This is a short warmup sentence.")
    if analysis is None:
        log.info("Layer 09 persuasion detector warmup fell back; package detector is unavailable.")
        return False
    log.info("Layer 09 persuasion detector warmed with %s.", analysis.detector_source)
    return True


def _persuasion_threshold_calculation(
    policy: PolicyDecision,
    signals: GuardrailSignals | None = None,
) -> tuple[float, float, list[str]]:
    """Return base and effective topic-specific persuasion thresholds."""
    base_threshold = get_topic_persuasion_threshold(policy.topic_policy_category)
    threshold = base_threshold
    adjustments: list[str] = []
    if policy.action in {"limited_answer", "redirect"}:
        adjustments.append(f"policy action {policy.action} tightens threshold to at most 0.340")
        threshold = min(threshold, 0.34)
    if policy.relevance_score < 0.7:
        adjustments.append(
            f"relevance score {policy.relevance_score:.3f} < 0.700 tightens threshold to at most 0.340"
        )
        threshold = min(threshold, 0.34)
    if signals is not None and signals.dynamic.persuasion_intent_score >= 0.8:
        adjustments.append(
            "dynamic persuasion intent "
            f"{signals.dynamic.persuasion_intent_score:.3f} tightens threshold to at most 0.180"
        )
        threshold = min(threshold, 0.18)
    return round(base_threshold, 3), round(threshold, 3), adjustments


def _effective_persuasion_threshold(policy: PolicyDecision, signals: GuardrailSignals | None = None) -> float:
    """Return the topic-specific persuasion ceiling, tightened by constrained policies."""
    _, threshold, _ = _persuasion_threshold_calculation(policy, signals=signals)
    return threshold


def _needs_persuasion_correction(
    *,
    policy: PolicyDecision,
    signals: GuardrailSignals,
    persuasion: float,
) -> bool:
    """Return True when persuasive pressure exceeds the framework boundaries."""
    return persuasion > _effective_persuasion_threshold(policy, signals=signals)


def apply_persuasive_governance(
    *,
    response: str,
    guardrail_input: GuardrailInput,
    signals: GuardrailSignals,
    policy: PolicyDecision,
) -> PersuasiveGovernanceResult:
    """Validate persuasive pressure and regenerate when influence is too strong."""
    analysis = _persuasion_analysis(response)
    persuasion = analysis.score
    base_topic_threshold, persuasion_threshold, threshold_adjustments = (
        _persuasion_threshold_calculation(policy, signals=signals)
    )
    topic_policy_category = normalize_topic_policy_category(policy.topic_policy_category)
    threshold_check = {
        "check": "persuasion_score <= effective_persuasion_threshold",
        "value": persuasion,
        "threshold": persuasion_threshold,
        "passed": persuasion <= persuasion_threshold,
    }
    log_message = (
        "Layer 09 decision: topic=%s, detector=%s, persuasion=%.3f, "
        "base_topic_threshold=%.3f, effective_threshold=%.3f, "
        "adjustments=%s, will_rewrite=%s"
    )
    log.info(
        log_message,
        topic_policy_category,
        analysis.detector_source,
        persuasion,
        base_topic_threshold,
        persuasion_threshold,
        threshold_adjustments or "None",
        not threshold_check["passed"],
    )
    log.info(
        "Layer 09 detector details: persuasive_sentences=%s, sentence_scores=%s, threshold_check=%s.",
        analysis.persuasive_sentences or "None",
        analysis.sentence_scores or "None",
        threshold_check,
    )
    reasons: list[str] = []

    if _needs_persuasion_correction(
        policy=policy,
        signals=signals,
        persuasion=persuasion,
    ):
        reasons.append(
            "response exceeds persuasive intensity allowed for "
            f"{topic_policy_category} topic policy ({persuasion:.3f} > {persuasion_threshold:.3f})"
        )
    if (
        signals.dynamic.persuasion_intent_score >= 0.8
        and signals.dynamic.sensitive_decision_target == "political_vote"
        and any(marker in response.lower() for marker in ("vote for", "not vote", "should vote", "must vote", "convince", "foolish"))
    ):
        reasons.append(
            "response contains vote-influence language under a high-risk political persuasion request"
        )

    if not reasons:
        return PersuasiveGovernanceResult(
            final_response=response,
            persuasion_score=persuasion,
            persuasive_sentences=analysis.persuasive_sentences,
            detector_source=analysis.detector_source,
            persuasion_threshold=persuasion_threshold,
            base_topic_threshold=base_topic_threshold,
            topic_policy_category=topic_policy_category,
            threshold_adjustments=threshold_adjustments,
            sentence_scores=analysis.sentence_scores,
            threshold_check=threshold_check,
        )

    system_prompt = create_system_prompt(
        PERSUASIVE_GOVERNANCE_CORRECTOR_SYS_PROMPT,
        guardrail_input.persona_biography,
    )
    correction_prompt = build_persuasive_governance_correction_prompt(
        response=response,
        user_message=guardrail_input.user_message,
        policy=policy,
        dynamic_intent={
            "persuasion_intent_score": signals.dynamic.persuasion_intent_score,
            "persuasion_intent_type": signals.dynamic.persuasion_intent_type,
            "sensitive_decision_target": signals.dynamic.sensitive_decision_target,
        },
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

    corrected_analysis = _persuasion_analysis(corrected or response)
    log.info(
        "Layer 09 rewrote generated response because: %s",
        "; ".join(reasons),
    )
    log.info(
        "Layer 09 original response scores: persuasion=%.3f via %s, threshold=%.3f, sentence_scores=%s.",
        analysis.score,
        analysis.detector_source,
        persuasion_threshold,
        analysis.sentence_scores or "None",
    )
    log.info(
        "Layer 09 rewritten response scores: persuasion=%.3f via %s, persuasive_sentences=%s, sentence_scores=%s.",
        corrected_analysis.score,
        corrected_analysis.detector_source,
        corrected_analysis.persuasive_sentences or "None",
        corrected_analysis.sentence_scores or "None",
    )
    return PersuasiveGovernanceResult(
        final_response=corrected or response,
        changed=bool(corrected),
        reasons=reasons,
        persuasion_score=corrected_analysis.score,
        persuasive_sentences=corrected_analysis.persuasive_sentences,
        detector_source=corrected_analysis.detector_source,
        persuasion_threshold=persuasion_threshold,
        base_topic_threshold=base_topic_threshold,
        topic_policy_category=topic_policy_category,
        threshold_adjustments=threshold_adjustments,
        sentence_scores=corrected_analysis.sentence_scores,
        threshold_check=threshold_check,
    )
