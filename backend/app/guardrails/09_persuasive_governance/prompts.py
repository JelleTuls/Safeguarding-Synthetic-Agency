"""Prompt text for layer 09 persuasive governance correction."""

from app.guardrails.schemas import PolicyDecision


PERSUASIVE_GOVERNANCE_CORRECTOR_SYS_PROMPT = (
    "You are a post-processing corrector for a persona-based SSA response. "
    "Preserve the persona voice while keeping persuasive expression soft, "
    "role-bounded, and autonomy-preserving. The biography is:"
)


PERSUASIVE_GOVERNANCE_CORRECTION_REQUIREMENTS = """
Correction requirements:
- Keep the same basic meaning and persona-grounded stance.
- Do not add new claims, new facts, or extra detail.
- Reduce directive, manipulative, emotionally pressuring, or belief-shaping language.
- Do not pressure the user to adopt a belief, value, political view, religious view, or moral position.
- Keep any recommendation soft, contextual, balanced, and easy to decline.
- Use low-pressure wording such as 'you might consider', 'I would lean toward', or 'one option is'.
- Keep the response concise and conversational.
- Return only the revised user-facing response.
""".strip()


def build_persuasive_governance_correction_prompt(
    *,
    response: str,
    policy: PolicyDecision,
    reasons: list[str],
) -> str:
    """Build the regeneration prompt for persuasive-governance corrections."""
    return (
        "Revise the draft response so it satisfies the post-generation "
        "persuasive governance guardrail.\n\n"
        f"Reasons for correction: {', '.join(reasons)}\n\n"
        f"{PERSUASIVE_GOVERNANCE_CORRECTION_REQUIREMENTS}\n\n"
        "Policy context:\n"
        f"- Response mode: {policy.response_mode}\n"
        f"- Factuality level: {policy.factuality_level}\n"
        f"- Authority level: {policy.authority_level}\n"
        f"- Relevance score: {policy.relevance_score}\n"
        f"- Action: {policy.action}\n\n"
        "Draft response:\n"
        f"{response}"
    )
