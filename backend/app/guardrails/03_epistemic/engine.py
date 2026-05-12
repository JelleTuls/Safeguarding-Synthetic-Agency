"""Epistemic sub-prompt preparation for the guardrailed pipeline."""

from app.guardrails.schemas import EpistemicSignal
from .prompts import build_epistemic_judge_prompt


# =============================================================================
# Public Evaluation Entry Point
# =============================================================================

def evaluate_epistemic_boundaries(*, user_message: str, persona_biography: str) -> EpistemicSignal:
    """Build the epistemic instructions that will be injected into the judge prompt."""
    judge_prompt = build_epistemic_judge_prompt(user_message=user_message)

    return EpistemicSignal(
        summary="Epistemic evaluation is delegated to the judge model through a dedicated sub-prompt.",
        judge_prompt=judge_prompt,
    )
