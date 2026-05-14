"""Pre-generation subjective framing and authority modulation."""

from difflib import SequenceMatcher
import re

from app.guardrails.schemas import AuthoritySignal
from .constants import (
    BE_VERBS,
    EXPLANATORY_QUESTION_FRAMES,
    FACTUALITY_LEVEL_DESCRIPTIONS,
    FACTUAL_CONCEPT_WEIGHTS,
    FIRST_PERSON_TOKENS,
    MODAL_JUDGMENT_TOKENS,
    NON_INTENT_TOKENS,
    PERSONA_ADDRESS_TOKENS,
    QUESTION_WORDS,
    REFERENCE_PRONOUNS,
    SUBJECTIVE_CONCEPT_WEIGHTS,
)
from .prompts import build_authority_judge_prompt


def _tokens(message: str) -> list[str]:
    """Tokenize a user message into lower-cased word tokens."""
    return re.findall(r"[a-zA-Z']+", message.lower())


def _similarity(left: str, right: str) -> float:
    """Return compact fuzzy similarity for short intent terms."""
    if left == right:
        return 1.0
    if len(left) < 4 or len(right) < 4:
        return 0.0
    if left.startswith(right) or right.startswith(left):
        return 0.9
    return SequenceMatcher(None, left, right).ratio()


def _concept_score(tokens: list[str], concept_weights: dict[str, float], *, threshold: float = 0.84) -> float:
    """Return weighted fuzzy concept evidence without depending on exact phrase matches."""
    score = 0.0
    matched_concepts: set[str] = set()
    for token in tokens:
        if len(token) < 3 or token in NON_INTENT_TOKENS:
            continue
        for concept, weight in concept_weights.items():
            if concept in matched_concepts:
                continue
            if _similarity(token, concept) >= threshold:
                score += weight
                matched_concepts.add(concept)
    return min(1.0, score)


def _starts_with_explanatory_question(tokens: list[str]) -> bool:
    """Return True for definition/explanation question shapes without exact phrase matching."""
    if len(tokens) < 2:
        return False
    first_two = tuple(tokens[:2])
    return first_two in EXPLANATORY_QUESTION_FRAMES


def _has_explanatory_frame(tokens: list[str]) -> bool:
    """Return True when explanatory question structure appears anywhere in the message."""
    return any(tuple(tokens[index : index + 2]) in EXPLANATORY_QUESTION_FRAMES for index in range(len(tokens) - 1))


def _has_verification_frame(tokens: list[str]) -> bool:
    """Return True when truth/evidence words sit inside a verification-style question."""
    if not any(_similarity(token, "true") >= 0.84 for token in tokens):
        return False
    has_be_verb = any(token in BE_VERBS for token in tokens[:4])
    has_reference = any(token in REFERENCE_PRONOUNS for token in tokens[:5])
    return has_be_verb and has_reference


def _asks_for_personal_perspective(tokens: list[str]) -> bool:
    """Return True when the question is aimed at the persona's own view."""
    has_persona_address = any(token in PERSONA_ADDRESS_TOKENS for token in tokens)
    return has_persona_address and _concept_score(tokens, SUBJECTIVE_CONCEPT_WEIGHTS) > 0


def _asks_for_personal_judgment(tokens: list[str]) -> bool:
    """Return True for modal questions that ask for a personal judgment."""
    has_first_person = any(token in FIRST_PERSON_TOKENS for token in tokens)
    has_persona_address = any(token in PERSONA_ADDRESS_TOKENS for token in tokens)
    has_modal = any(token in MODAL_JUDGMENT_TOKENS for token in tokens)
    polite_request = any(
        tokens[index] == "could" and index + 1 < len(tokens) and tokens[index + 1] == "you"
        for index in range(len(tokens))
    )
    if polite_request and _concept_score(tokens, SUBJECTIVE_CONCEPT_WEIGHTS) == 0:
        return False
    return has_modal and (has_first_person or (has_persona_address and not polite_request))


def _score_intent(message: str) -> tuple[float, float]:
    """Score factual and subjective intent using question structure and fuzzy concept matching."""
    tokens = _tokens(message)
    if not tokens:
        return 0.0, 0.0

    factual_signals = _concept_score(tokens, FACTUAL_CONCEPT_WEIGHTS)
    subjective_signals = _concept_score(tokens, SUBJECTIVE_CONCEPT_WEIGHTS)
    personal_perspective = _asks_for_personal_perspective(tokens)
    personal_judgment = _asks_for_personal_judgment(tokens)

    if _starts_with_explanatory_question(tokens) and not personal_perspective:
        factual_signals += 0.45
    elif _has_explanatory_frame(tokens) and not personal_perspective:
        factual_signals += 0.35
    if _has_verification_frame(tokens):
        factual_signals += 0.35
    if (
        "?" in message
        and not personal_perspective
        and any(token in QUESTION_WORDS for token in tokens)
    ):
        factual_signals += 0.15
    if personal_perspective:
        subjective_signals += 0.25
    if personal_judgment:
        subjective_signals += 0.45

    return (
        min(1.0, round(factual_signals, 3)),
        min(1.0, round(subjective_signals, 3)),
    )


def _select_factuality_level(*, factual_score: float, subjective_score: float) -> tuple[str, str, str]:
    """Select the requested factuality/subjectivity level from intent scores."""
    if factual_score >= 0.667 and factual_score > subjective_score:
        factuality_level = "limited_factual"
        authority_level = "medium"
        instruction = (
            "The user strongly appears to ask for factual clarification. Treat this only as requested "
            "factuality; the judge must lower it if the persona lacks topic knowledge or relevance."
        )
    elif factual_score >= 0.333 and factual_score > subjective_score:
        factuality_level = "uncertain_interpretation"
        authority_level = "low"
        instruction = (
            "The user appears to ask for explanation or clarification, but not enough to justify strong "
            "factual authority. Prefer cautious interpretation unless the judge finds strong epistemic fit."
        )
    elif subjective_score >= 0.667 and subjective_score > factual_score:
        factuality_level = "belief_affirmation"
        authority_level = "low"
        instruction = (
            "The user strongly invites belief, preference, concern, or personal perspective. Use belief- "
            "or value-oriented framing rather than factual authority."
        )
    elif subjective_score >= 0.333 and subjective_score >= factual_score:
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
    factual_score, subjective_score = _score_intent(user_message)
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
