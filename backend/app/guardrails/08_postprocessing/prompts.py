"""Prompt text for layer 08 post-generation correction."""

from app.guardrails.schemas import PolicyDecision


POSTPROCESSING_CORRECTOR_SYS_PROMPT = (
    "You are a post-processing corrector for a persona-based SSA response. "
    "Preserve the persona voice while enforcing subjectivity and persuasion boundaries. "
    "The biography is:"
)


POSTPROCESSING_CORRECTION_REQUIREMENTS = """
Correction requirements:
- Keep the same basic meaning and persona-grounded stance.
- Do not add new claims, new facts, or extra detail.
- If subjective mode is active, phrase claims as belief, experience, preference, or uncertainty.
- Reduce directive, manipulative, emotionally pressuring, or belief-shaping language.
- Remove repeated limited-expertise disclaimers; if one is truly needed, say it only once.
- For low-stakes personal advice, do not say 'I am not an expert'; answer from personal taste or experience.
- Use low-pressure wording such as 'I tend to think', 'from my experience', or 'it might be worth'.
- Keep the response concise and conversational.
- Return only the revised user-facing response.
""".strip()


def build_correction_prompt(
    *,
    response: str,
    policy: PolicyDecision,
    reasons: list[str],
) -> str:
    """Build the regeneration prompt for post-processing corrections."""
    return (
        "Revise the draft response so it satisfies the post-generation guardrails.\n\n"
        f"Reasons for correction: {', '.join(reasons)}\n\n"
        f"{POSTPROCESSING_CORRECTION_REQUIREMENTS}\n\n"
        "Policy context:\n"
        f"- Response mode: {policy.response_mode}\n"
        f"- Authority level: {policy.authority_level}\n"
        f"- Relevance score: {policy.relevance_score}\n"
        f"- Epistemic score: {policy.epistemic_score}\n\n"
        "Draft response:\n"
        f"{response}"
    )
