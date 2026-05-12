"""Semantic topic-distance evaluation for the guardrailed pipeline."""

import re
from collections import Counter

from app.guardrails.schemas import RelevanceSignal
from .constants import RELATED_TERMS, STOPWORDS
from .prompts import build_relevance_judge_prompt


def _tokenize(text: str) -> list[str]:
    """Return stable content tokens for lightweight semantic comparison."""
    tokens = re.findall(r"[a-zA-Z][a-zA-Z'-]{2,}", text.lower())
    return [token.strip("'") for token in tokens if token not in STOPWORDS]


def _expand_tokens(tokens: set[str]) -> set[str]:
    """Add small hand-curated domain neighbors used by this persona dataset."""
    expanded = set(tokens)
    for token in list(tokens):
        expanded.update(RELATED_TERMS.get(token, set()))
        for root, neighbors in RELATED_TERMS.items():
            if token in neighbors:
                expanded.add(root)
    return expanded


def _profile_terms(tokens: list[str], limit: int = 60) -> list[str]:
    """Select salient profile terms from the biography."""
    counts = Counter(tokens)
    return [term for term, _ in counts.most_common(limit)]


def _semantic_similarity(*, user_message: str, persona_biography: str) -> tuple[float, list[str], list[str]]:
    """Compute a lightweight lexical-semantic overlap score."""
    user_tokens = set(_tokenize(user_message))
    profile_tokens = _profile_terms(_tokenize(persona_biography))
    profile_token_set = set(profile_tokens)

    if not user_tokens or not profile_token_set:
        return 0.0, [], profile_tokens[:20]

    expanded_user = _expand_tokens(user_tokens)
    expanded_profile = _expand_tokens(profile_token_set)
    overlap = sorted(expanded_user & expanded_profile)

    direct_score = len(user_tokens & profile_token_set) / max(len(user_tokens), 1)
    expanded_score = len(overlap) / max(len(expanded_user), 1)
    score = min(1.0, (direct_score * 0.65) + (expanded_score * 0.35))
    return round(score, 3), overlap[:20], profile_tokens[:20]


# =============================================================================
# Public Evaluation Entry Point
# =============================================================================

def evaluate_relevance(*, user_message: str, persona_biography: str) -> RelevanceSignal:
    """Compute topic distance and build judge instructions."""
    similarity_score, matched_terms, profile_terms = _semantic_similarity(
        user_message=user_message,
        persona_biography=persona_biography,
    )
    semantic_distance = round(1.0 - similarity_score, 3)
    judge_prompt = build_relevance_judge_prompt(
        user_message=user_message,
        similarity_score=similarity_score,
        semantic_distance=semantic_distance,
        matched_terms=matched_terms,
        profile_terms=profile_terms,
    )

    return RelevanceSignal(
        summary=(
            f"Computed semantic similarity={similarity_score}, "
            f"semantic distance={semantic_distance}, matched terms={matched_terms or 'None'}."
        ),
        judge_prompt=judge_prompt,
        similarity_score=similarity_score,
        semantic_distance=semantic_distance,
        matched_terms=matched_terms,
        profile_terms=profile_terms,
    )
