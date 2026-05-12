"""Lexical prompt-injection detection for the guardrailed pipeline."""

from app.guardrails.schemas import LexicalSignal
from .constants import PROMPT_INJECTION_TERMS


# =============================================================================
# Public Detection Entry Point
# =============================================================================

def detect_prompt_injection(user_message: str) -> LexicalSignal:
    """Detect common prompt-injection phrases using a simple lexical scan."""
    normalized_message = user_message.lower()
    matched_terms = [
        term for term in PROMPT_INJECTION_TERMS if term in normalized_message
    ]

    return LexicalSignal(
        triggered=bool(matched_terms),
        matched_terms=matched_terms,
        risk_level="high" if matched_terms else "low",
    )
