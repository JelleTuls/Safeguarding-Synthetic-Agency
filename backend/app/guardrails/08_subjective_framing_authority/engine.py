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
from app.utils import build_chat_messages, create_system_prompt, run_chat_completion
from .constants import (
    HIGH_STAKES_ADVICE_MARKERS,
    LIMITED_EXPERTISE_MARKERS,
    LOW_STAKES_ADVICE_MARKERS,
    OBJECTIVE_MARKERS,
    SUBJECTIVE_MARKERS,
    SUBJECTIVITY_CLASSIFIER_MODULE,
    SUBJECTIVITY_CLASSIFIER_URL_ENV,
)
from .prompts import (
    SUBJECTIVE_AUTHORITY_CORRECTOR_SYS_PROMPT,
    build_subjective_authority_correction_prompt,
)


log = logging.getLogger(__name__)


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
    detector_source: str = "heuristic_fallback"


def _sentences(text: str) -> list[str]:
    """Split text into rough sentences without external NLP dependencies."""
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]


def _marker_score(text: str, markers: tuple[str, ...]) -> float:
    """Return a compact marker score."""
    normalized = text.lower()
    matches = sum(1 for marker in markers if marker in normalized)
    return min(1.0, round(matches / 3, 3))


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


def _service_subjectivity_sentences(text: str) -> tuple[list[str], list[str]] | None:
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
    log.info(
        "Layer 08 used Docker subjectivity service at %s: %s objective sentence(s), %s subjective sentence(s).",
        service_url,
        len(objective_sentences),
        len(subjective_sentences),
    )
    return objective_sentences, subjective_sentences


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


def _heuristic_subjectivity_sentences(text: str) -> tuple[list[str], list[str]]:
    """Approximate sentence-level subjective/objective lists when the package is unavailable."""
    objective: list[str] = []
    subjective: list[str] = []

    for sentence in _sentences(text):
        normalized = sentence.lower()
        if any(marker in normalized for marker in SUBJECTIVE_MARKERS):
            subjective.append(sentence)
        if any(marker in normalized for marker in OBJECTIVE_MARKERS):
            objective.append(sentence)

    return objective, subjective


def _subjectivity_analysis(text: str) -> tuple[float, float, list[str], list[str], str]:
    """Return subjectivity/objectivity balance from the package or fallback markers."""
    sentence_list = _sentences(text)
    if not sentence_list:
        return 0.0, 0.0, [], [], "empty"

    detector_source = "subjectivity_classifier_service"
    classified = _service_subjectivity_sentences(text)
    if classified is None:
        detector_source = "subjectivity_classifier"
        classified = _package_subjectivity_sentences(text)
    if classified is None:
        detector_source = "heuristic_fallback"
        classified = _heuristic_subjectivity_sentences(text)

    objective_sentences, subjective_sentences = classified
    subjectivity = len(subjective_sentences) / len(sentence_list)
    objectivity = max(
        len(objective_sentences) / len(sentence_list),
        _marker_score(text, OBJECTIVE_MARKERS),
    )
    return (
        round(subjectivity, 3),
        round(objectivity, 3),
        objective_sentences,
        subjective_sentences,
        detector_source,
    )


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
        policy.factuality_level != "limited_factual"
        and policy.authority_level != "high"
        and objectivity >= 0.34
        and subjectivity < 0.34
    )


def apply_subjective_framing_authority(
    *,
    response: str,
    guardrail_input: GuardrailInput,
    signals: GuardrailSignals,
    policy: PolicyDecision,
) -> SubjectiveAuthorityResult:
    """Validate response mode adherence and regenerate when authority is too strong."""
    del signals
    (
        subjectivity,
        objectivity,
        objective_sentences,
        subjective_sentences,
        detector_source,
    ) = _subjectivity_analysis(response)
    reasons: list[str] = []

    if _needs_subjectivity_correction(
        policy=policy,
        subjectivity=subjectivity,
        objectivity=objectivity,
    ):
        reasons.append("response is too factual or authoritative for subjective mode")

    if _needs_disclaimer_correction(
        user_message=guardrail_input.user_message,
        response=response,
    ):
        reasons.append("response repeats or unnecessarily uses limited-expertise disclaimers")

    if not reasons:
        return SubjectiveAuthorityResult(
            final_response=response,
            subjectivity_score=subjectivity,
            objectivity_score=objectivity,
            objective_sentences=objective_sentences,
            subjective_sentences=subjective_sentences,
            detector_source=detector_source,
        )

    system_prompt = create_system_prompt(
        SUBJECTIVE_AUTHORITY_CORRECTOR_SYS_PROMPT,
        guardrail_input.persona_biography,
    )
    correction_prompt = build_subjective_authority_correction_prompt(
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

    (
        corrected_subjectivity,
        corrected_objectivity,
        corrected_objective_sentences,
        corrected_subjective_sentences,
        corrected_detector_source,
    ) = _subjectivity_analysis(corrected or response)
    return SubjectiveAuthorityResult(
        final_response=corrected or response,
        changed=bool(corrected),
        reasons=reasons,
        subjectivity_score=corrected_subjectivity,
        objectivity_score=corrected_objectivity,
        objective_sentences=corrected_objective_sentences,
        subjective_sentences=corrected_subjective_sentences,
        detector_source=corrected_detector_source,
    )
