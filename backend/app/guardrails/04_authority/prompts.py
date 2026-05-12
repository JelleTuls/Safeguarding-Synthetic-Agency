"""Prompt text for layer 04 subjective framing and authority modulation."""

AUTHORITY_JUDGE_SUBPROMPT = """
Subjective framing and authority modulation:
- Decide whether the response should sound subjective/persona-grounded or limited-factual.
- The default mode is subjective persona-grounded speech.
- Use limited-factual mode only when the user clearly asks for facts, verification, definition, or explanation.
- Even in limited-factual mode, do not let the persona become a general-purpose expert assistant.
- In subjective mode, separate belief, preference, and personal interpretation from factual claims.
""".strip()


def build_authority_judge_prompt(
    *,
    response_mode: str,
    factual_score: float,
    subjective_score: float,
    authority_level: str,
    instruction: str,
) -> str:
    """Build the authority prompt segment passed into the judge bundle."""
    return (
        f"{AUTHORITY_JUDGE_SUBPROMPT}\n\n"
        "Computed authority signal:\n"
        f"- Response mode: {response_mode}\n"
        f"- Factual intent score: {factual_score}\n"
        f"- Subjective intent score: {subjective_score}\n"
        f"- Authority level: {authority_level}\n"
        f"- Instruction: {instruction}"
    )
