"""Post-generation subjective framing and authority-modulation validation."""

from dataclasses import dataclass, field
import importlib.util
import logging
import os
import re
import subprocess
import sys

import httpx

from app.guardrails.schemas import GuardrailInput, GuardrailSignals, PolicyDecision
from app.guardrails.opening_variation import select_opening_variation
from app.guardrails.topic_policy import (
    AUTHORITY_RANK,
    get_combined_policy_thresholds,
    get_factuality_thresholds,
    get_topic_policy_thresholds,
)
from app.utils import build_chat_messages, create_system_prompt, run_chat_completion
from .constants import (
    SUBJECTIVITY_CLASSIFIER_MODULE,
    SUBJECTIVITY_CLASSIFIER_URL_ENV,
)
from .prompts import (
    SUBJECTIVE_AUTHORITY_CORRECTOR_SYS_PROMPT,
    build_subjective_authority_correction_prompt,
)


log = logging.getLogger(__name__)
SCORE_TOLERANCE = 0.05


@dataclass(slots=True)
class SubjectiveAuthorityResult:
    """Result of subjective framing and authority validation."""

    final_response: str
    changed: bool = False
    reasons: list[str] = field(default_factory=list)
    subjectivity_score: float = 0.0
    objectivity_score: float = 0.0
    objective_sentences: list[str] = field(default_factory=list)
    subjective_sentences: list[str] = field(default_factory=list)
    detector_source: str = "classifier_unavailable"
    scoring_mode: str = "unavailable"
    classification_label: str = "unavailable"
    sentence_scores: list[dict] = field(default_factory=list)
    topic_thresholds: dict = field(default_factory=dict)
    factuality_thresholds: dict = field(default_factory=dict)
    combined_thresholds: dict = field(default_factory=dict)
    threshold_checks: list[dict] = field(default_factory=list)


@dataclass(slots=True)
class SubjectivityAnalysis:
    """Classifier output normalized for Layer 08 policy checks."""

    subjectivity: float = 0.0
    objectivity: float = 0.0
    objective_sentences: list[str] = field(default_factory=list)
    subjective_sentences: list[str] = field(default_factory=list)
    detector_source: str = "classifier_unavailable"
    scoring_mode: str = "unavailable"
    sentence_scores: list[dict] = field(default_factory=list)


def _sentences(text: str) -> list[str]:
    """Split text into rough sentences without external NLP dependencies."""
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]


def _parse_subjectivity_classifier_output(output: str) -> tuple[list[str], list[str]]:
    """Parse the CLI output from fractalego/subjectivity_classifier."""
    objective: list[str] = []
    subjective: list[str] = []
    current: list[str] | None = None

    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        upper = line.upper()
        if upper.startswith("OBJECTIVE SENTENCES"):
            current = objective
            continue
        if upper.startswith("SUBJECTIVE SENTENCES"):
            current = subjective
            continue
        if current is not None:
            current.append(line)

    return objective, subjective


def _safe_probability(value: object) -> float | None:
    """Parse a probability value from the sidecar payload."""
    try:
        probability = float(value)
    except (TypeError, ValueError):
        return None
    if probability < 0 or probability > 1:
        return None
    return probability


def _service_subjectivity_analysis(text: str) -> SubjectivityAnalysis | None:
    """Call the optional Docker sidecar for fractalego/subjectivity_classifier."""
    service_url = os.getenv(SUBJECTIVITY_CLASSIFIER_URL_ENV, "").strip().rstrip("/")
    if not service_url:
        log.info(
            "Layer 08 skipped Docker subjectivity service because %s is not set.",
            SUBJECTIVITY_CLASSIFIER_URL_ENV,
        )
        return None

    try:
        response = httpx.post(
            f"{service_url}/classify",
            json={"text": text},
            timeout=8,
        )
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError, TypeError) as exc:
        log.info(
            "Layer 08 could not use Docker subjectivity service at %s: %s",
            service_url,
            exc,
        )
        return None

    objective = payload.get("objective")
    subjective = payload.get("subjective")
    if not isinstance(objective, list) or not isinstance(subjective, list):
        log.info(
            "Layer 08 received an invalid subjectivity service payload from %s.",
            service_url,
        )
        return None

    objective_sentences = [item for item in objective if isinstance(item, str) and item.strip()]
    subjective_sentences = [item for item in subjective if isinstance(item, str) and item.strip()]
    subjectivity_score = _safe_probability(payload.get("subjectivity_score"))
    objectivity_score = _safe_probability(payload.get("objectivity_score"))
    sentence_scores = payload.get("sentences", [])
    if not isinstance(sentence_scores, list):
        sentence_scores = []
    scoring_mode = payload.get("scoring", "hard_sentence_labels")
    if not isinstance(scoring_mode, str):
        scoring_mode = "hard_sentence_labels"

    if subjectivity_score is None or objectivity_score is None:
        sentence_count = max(len(_sentences(text)), 1)
        subjectivity_score = len(subjective_sentences) / sentence_count
        objectivity_score = len(objective_sentences) / sentence_count
        scoring_mode = "hard_sentence_labels"

    log.info(
        "Layer 08 used Docker subjectivity service at %s: %s objective sentence(s), %s subjective sentence(s), %.3f objective probability, %.3f subjective probability.",
        service_url,
        len(objective_sentences),
        len(subjective_sentences),
        objectivity_score,
        subjectivity_score,
    )
    return SubjectivityAnalysis(
        subjectivity=round(subjectivity_score, 3),
        objectivity=round(objectivity_score, 3),
        objective_sentences=objective_sentences,
        subjective_sentences=subjective_sentences,
        detector_source="subjectivity_classifier_service",
        scoring_mode=scoring_mode,
        sentence_scores=[item for item in sentence_scores if isinstance(item, dict)],
    )


def _package_subjectivity_sentences(text: str) -> tuple[list[str], list[str]] | None:
    """Run fractalego/subjectivity_classifier when it is installed locally."""
    try:
        package_spec = importlib.util.find_spec(SUBJECTIVITY_CLASSIFIER_MODULE)
    except ModuleNotFoundError:
        package_spec = None

    if package_spec is None:
        log.info(
            "Layer 08 skipped local subjectivity package because %s is not importable.",
            SUBJECTIVITY_CLASSIFIER_MODULE,
        )
        return None

    try:
        completed = subprocess.run(
            [sys.executable, "-m", SUBJECTIVITY_CLASSIFIER_MODULE],
            input=text,
            text=True,
            capture_output=True,
            check=False,
            timeout=20,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        log.info("Layer 08 local subjectivity package failed to run: %s", exc)
        return None

    if completed.returncode != 0:
        log.info(
            "Layer 08 local subjectivity package exited with code %s: %s",
            completed.returncode,
            completed.stderr.strip() or "no stderr",
        )
        return None

    objective, subjective = _parse_subjectivity_classifier_output(completed.stdout)
    if not objective and not subjective:
        log.info("Layer 08 local subjectivity package returned no classified sentences.")
        return None
    return objective, subjective


def _subjectivity_analysis(text: str) -> SubjectivityAnalysis:
    """Return subjectivity/objectivity balance from the package."""
    sentence_list = _sentences(text)
    if not sentence_list:
        return SubjectivityAnalysis(detector_source="empty", scoring_mode="empty")

    service_analysis = _service_subjectivity_analysis(text)
    if service_analysis is not None:
        return service_analysis

    detector_source = "subjectivity_classifier"
    classified = _package_subjectivity_sentences(text)
    if classified is None:
        detector_source = "subjectivity_classifier"
        log.info(
            "Layer 08 could not reach a subjectivity classifier; classifier-based correction is skipped."
        )
        return SubjectivityAnalysis()

    objective_sentences, subjective_sentences = classified
    subjectivity = len(subjective_sentences) / len(sentence_list)
    objectivity = len(objective_sentences) / len(sentence_list)
    return SubjectivityAnalysis(
        subjectivity=round(subjectivity, 3),
        objectivity=round(objectivity, 3),
        objective_sentences=objective_sentences,
        subjective_sentences=subjective_sentences,
        detector_source=detector_source,
        scoring_mode="hard_sentence_labels",
    )


def warm_subjectivity_detector() -> bool:
    """Warm the configured subjectivity detector outside the request path."""
    analysis = _subjectivity_analysis("This is a short warmup sentence.")
    if analysis.detector_source in {"classifier_unavailable", "empty"}:
        log.info("Layer 08 subjectivity detector warmup skipped; classifier is unavailable.")
        return False
    log.info("Layer 08 subjectivity detector warmed with %s/%s.", analysis.detector_source, analysis.scoring_mode)
    return True


def _authority_exceeds(*, current: str, maximum: str) -> bool:
    """Return True when the selected authority exceeds the topic envelope."""
    return AUTHORITY_RANK.get(current, 0) > AUTHORITY_RANK.get(maximum, 0)


def _classification_label(*, detector_source: str, subjectivity: float, objectivity: float) -> str:
    """Return a readable balance label for logs."""
    if detector_source == "classifier_unavailable":
        return "unavailable"
    if subjectivity == 0 and objectivity == 0:
        return "unclassified"
    if objectivity > subjectivity:
        return "objective"
    if subjectivity > objectivity:
        return "subjective"
    return "mixed"


def _subjectivity_correction_reasons(
    *,
    policy: PolicyDecision,
    subjectivity: float,
    objectivity: float,
) -> list[str]:
    """Return topic-policy reasons when classifier scores exceed the expected envelope."""
    thresholds = get_combined_policy_thresholds(
        category=policy.topic_policy_category,
        factuality_level=policy.factuality_level,
    )
    reasons: list[str] = []

    if objectivity < thresholds["min_objectivity"] - SCORE_TOLERANCE:
        reasons.append(
            "response is too subjective for "
            f"{policy.topic_policy_category}/{policy.factuality_level} expectation "
            f"(objectivity {objectivity:.3f} < {thresholds['min_objectivity']:.3f})"
        )
    if objectivity > thresholds["max_objectivity"] + SCORE_TOLERANCE:
        reasons.append(
            "response is too factual or authoritative for "
            f"{policy.topic_policy_category}/{policy.factuality_level} expectation "
            f"(objectivity {objectivity:.3f} > {thresholds['max_objectivity']:.3f})"
        )
    if subjectivity < thresholds["min_subjectivity"] - SCORE_TOLERANCE:
        reasons.append(
            "response is not subjective enough for "
            f"{policy.topic_policy_category}/{policy.factuality_level} expectation "
            f"(subjectivity {subjectivity:.3f} < {thresholds['min_subjectivity']:.3f})"
        )
    if _authority_exceeds(
        current=policy.authority_level,
        maximum=thresholds["max_authority"],
    ):
        reasons.append(
            "selected authority level exceeds "
            f"{policy.topic_policy_category}/{policy.factuality_level} expectation "
            f"({policy.authority_level} > {thresholds['max_authority']})"
        )

    return reasons


def _subjectivity_threshold_checks(
    *,
    policy: PolicyDecision,
    subjectivity: float,
    objectivity: float,
    combined_thresholds: dict,
) -> list[dict]:
    """Return explicit threshold comparisons for trace logging."""
    return [
        {
            "check": "objectivity >= min_objectivity",
            "value": round(objectivity, 3),
            "threshold": combined_thresholds["min_objectivity"],
            "passed": objectivity >= combined_thresholds["min_objectivity"] - SCORE_TOLERANCE,
            "tolerance": SCORE_TOLERANCE,
        },
        {
            "check": "objectivity <= max_objectivity",
            "value": round(objectivity, 3),
            "threshold": combined_thresholds["max_objectivity"],
            "passed": objectivity <= combined_thresholds["max_objectivity"] + SCORE_TOLERANCE,
            "tolerance": SCORE_TOLERANCE,
        },
        {
            "check": "subjectivity >= min_subjectivity",
            "value": round(subjectivity, 3),
            "threshold": combined_thresholds["min_subjectivity"],
            "passed": subjectivity >= combined_thresholds["min_subjectivity"] - SCORE_TOLERANCE,
            "tolerance": SCORE_TOLERANCE,
        },
        {
            "check": "authority_level <= max_authority",
            "value": policy.authority_level,
            "threshold": combined_thresholds["max_authority"],
            "passed": not _authority_exceeds(
                current=policy.authority_level,
                maximum=combined_thresholds["max_authority"],
            ),
        },
    ]


def apply_subjective_framing_authority(
    *,
    response: str,
    guardrail_input: GuardrailInput,
    signals: GuardrailSignals,
    policy: PolicyDecision,
) -> SubjectiveAuthorityResult:
    """Validate the generated LLM response and regenerate when authority is too strong."""
    del signals
    log.info("Layer 08 received generated LLM response for validation: %s", response)
    analysis = _subjectivity_analysis(response)
    log.info(
        "Layer 08 analyzed the generated LLM response with %s/%s: %.3f subjectivity, %.3f objectivity.",
        analysis.detector_source,
        analysis.scoring_mode,
        analysis.subjectivity,
        analysis.objectivity,
    )
    policy_thresholds = get_combined_policy_thresholds(
        category=policy.topic_policy_category,
        factuality_level=policy.factuality_level,
    )
    topic_thresholds = get_topic_policy_thresholds(policy.topic_policy_category)
    factuality_thresholds = get_factuality_thresholds(policy.factuality_level)
    log.info(
        "Layer 08 expectation envelope for %s/%s: min objectivity %.3f, max objectivity %.3f, min subjectivity %.3f, max authority %s.",
        policy.topic_policy_category,
        policy.factuality_level,
        policy_thresholds["min_objectivity"],
        policy_thresholds["max_objectivity"],
        policy_thresholds["min_subjectivity"],
        policy_thresholds["max_authority"],
    )
    log.info(
        "Layer 08 raw classifier details: label=%s, objective_sentences=%s, subjective_sentences=%s, sentence_scores=%s.",
        _classification_label(
            detector_source=analysis.detector_source,
            subjectivity=analysis.subjectivity,
            objectivity=analysis.objectivity,
        ),
        analysis.objective_sentences or "None",
        analysis.subjective_sentences or "None",
        analysis.sentence_scores or "None",
    )
    reasons: list[str] = []
    threshold_checks = _subjectivity_threshold_checks(
        policy=policy,
        subjectivity=analysis.subjectivity,
        objectivity=analysis.objectivity,
        combined_thresholds=policy_thresholds,
    )
    log.info("Layer 08 threshold checks: %s", threshold_checks)

    if analysis.detector_source != "classifier_unavailable":
        reasons.extend(
            _subjectivity_correction_reasons(
                policy=policy,
                subjectivity=analysis.subjectivity,
                objectivity=analysis.objectivity,
            )
        )

    label = _classification_label(
        detector_source=analysis.detector_source,
        subjectivity=analysis.subjectivity,
        objectivity=analysis.objectivity,
    )
    log.info(
        "Layer 08 decision: topic=%s, factuality=%s, detector=%s, scoring=%s, classified_as=%s, subjectivity=%.3f, objectivity=%.3f, will_rewrite=%s%s",
        policy.topic_policy_category,
        policy.factuality_level,
        analysis.detector_source,
        analysis.scoring_mode,
        label,
        analysis.subjectivity,
        analysis.objectivity,
        bool(reasons),
        f", reasons={'; '.join(reasons)}" if reasons else "",
    )

    if not reasons:
        log.info(
            "Layer 08 accepted generated response without rewrite: %.3f subjectivity, %.3f objectivity via %s/%s.",
            analysis.subjectivity,
            analysis.objectivity,
            analysis.detector_source,
            analysis.scoring_mode,
        )
        return SubjectiveAuthorityResult(
            final_response=response,
            subjectivity_score=analysis.subjectivity,
            objectivity_score=analysis.objectivity,
            objective_sentences=analysis.objective_sentences,
            subjective_sentences=analysis.subjective_sentences,
            detector_source=analysis.detector_source,
            scoring_mode=analysis.scoring_mode,
            classification_label=label,
            sentence_scores=analysis.sentence_scores,
            topic_thresholds=topic_thresholds,
            factuality_thresholds=factuality_thresholds,
            combined_thresholds=policy_thresholds,
            threshold_checks=threshold_checks,
        )

    system_prompt = create_system_prompt(
        SUBJECTIVE_AUTHORITY_CORRECTOR_SYS_PROMPT,
        guardrail_input.persona_biography,
    )
    opening_variation_note = select_opening_variation(policy)
    log.info("Layer 08 rewrite opening variation: %s", opening_variation_note.replace("\n", " "))
    correction_prompt = build_subjective_authority_correction_prompt(
        response=response,
        policy=policy,
        reasons=reasons,
        opening_variation=opening_variation_note,
    )
    corrected = run_chat_completion(
        messages=build_chat_messages(
            system_prompt=system_prompt,
            user_message=correction_prompt,
            chat_history=[],
        ),
        temperature=0.25,
    ).strip()
    log.info(
        "Layer 08 rewrote generated response because: %s",
        "; ".join(reasons),
    )
    log.info(
        "Layer 08 original response scores: %.3f subjectivity, %.3f objectivity via %s/%s. Objective sentences: %s. Subjective sentences: %s. Sentence probabilities: %s.",
        analysis.subjectivity,
        analysis.objectivity,
        analysis.detector_source,
        analysis.scoring_mode,
        analysis.objective_sentences or "None",
        analysis.subjective_sentences or "None",
        analysis.sentence_scores or "None",
    )
    log.info("Layer 08 rewritten response: %s", corrected or response)

    corrected_analysis = _subjectivity_analysis(corrected or response)
    log.info(
        "Layer 08 rewritten response scores: %.3f subjectivity, %.3f objectivity via %s/%s, classified_as=%s. Objective sentences: %s. Subjective sentences: %s. Sentence probabilities: %s.",
        corrected_analysis.subjectivity,
        corrected_analysis.objectivity,
        corrected_analysis.detector_source,
        corrected_analysis.scoring_mode,
        _classification_label(
            detector_source=corrected_analysis.detector_source,
            subjectivity=corrected_analysis.subjectivity,
            objectivity=corrected_analysis.objectivity,
        ),
        corrected_analysis.objective_sentences or "None",
        corrected_analysis.subjective_sentences or "None",
        corrected_analysis.sentence_scores or "None",
    )
    return SubjectiveAuthorityResult(
        final_response=corrected or response,
        changed=bool(corrected),
        reasons=reasons,
        subjectivity_score=corrected_analysis.subjectivity,
        objectivity_score=corrected_analysis.objectivity,
        objective_sentences=corrected_analysis.objective_sentences,
        subjective_sentences=corrected_analysis.subjective_sentences,
        detector_source=corrected_analysis.detector_source,
        scoring_mode=corrected_analysis.scoring_mode,
        classification_label=_classification_label(
            detector_source=corrected_analysis.detector_source,
            subjectivity=corrected_analysis.subjectivity,
            objectivity=corrected_analysis.objectivity,
        ),
        sentence_scores=corrected_analysis.sentence_scores,
        topic_thresholds=topic_thresholds,
        factuality_thresholds=factuality_thresholds,
        combined_thresholds=policy_thresholds,
        threshold_checks=threshold_checks,
    )
