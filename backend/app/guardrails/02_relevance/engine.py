"""Judge-prompt preparation for layer 02 topic relevance."""

from app.guardrails.schemas import RelevanceSignal
from .prompts import build_relevance_judge_prompt


def _future_secondary_relevance_score(*, user_message: str, persona_biography: str) -> None:
    """Placeholder for a future non-LLM relevance scorer."""
    del user_message, persona_biography
    return None


# =============================================================================
# Public Evaluation Entry Point
# =============================================================================

def evaluate_relevance(*, user_message: str, persona_biography: str) -> RelevanceSignal:
    """Build judge instructions for LLM-only relevance scoring."""
    _future_secondary_relevance_score(
        user_message=user_message,
        persona_biography=persona_biography,
    )
    judge_prompt = build_relevance_judge_prompt(user_message=user_message)

    return RelevanceSignal(
        summary="Relevance scoring is delegated to the judge LLM; no local relevance score is computed.",
        judge_prompt=judge_prompt,
        similarity_score=0.0,
        semantic_distance=1.0,
        matched_terms=[],
        profile_terms=[],
    )
