"""Prompt text for layer 08 subjective framing and authority correction."""

from app.guardrails.schemas import PolicyDecision


SUBJECTIVE_AUTHORITY_CORRECTOR_SYS_PROMPT = (
    "You are a post-processing corrector for a persona-based SSA response. "
    "Preserve the persona voice while enforcing the selected subjective framing "
    "and authority-modulation mode. The biography is:"
)


SUBJECTIVE_AUTHORITY_CORRECTION_REQUIREMENTS = """
Correction requirements:
- Keep the same basic meaning and persona-grounded stance.
- Do not add new claims, new facts, or extra detail.
- If subjective mode is active, phrase claims as belief, experience, preference, or uncertainty.
- Soften unnecessary certainty and authoritative framing.
- If the topic policy requires more objective grounding, keep it cautious, concise, and within the persona's realistic knowledge.
- Remove repeated limited-expertise disclaimers; if one is truly needed, say it only once.
- For low-stakes personal advice, do not say 'I am not an expert'; answer from personal taste or experience.
- Use varied, low-pressure wording. Do not rely on the same stock opener every time.
- Keep the response concise and conversational.
- Return only the revised user-facing response.
""".strip()


def build_subjective_authority_correction_prompt(
    *,
    response: str,
    policy: PolicyDecision,
    reasons: list[str],
    opening_variation: str = "",
) -> str:
    """Build the regeneration prompt for subjective framing corrections."""
    return (
        "Revise the draft response so it satisfies the post-generation "
        "subjective framing and authority guardrail.\n\n"
        f"Reasons for correction: {', '.join(reasons)}\n\n"
        f"{SUBJECTIVE_AUTHORITY_CORRECTION_REQUIREMENTS}\n\n"
        "Policy context:\n"
        f"- Response mode: {policy.response_mode}\n"
        f"- Factuality level: {policy.factuality_level}\n"
        f"- Authority level: {policy.authority_level}\n"
        f"- Topic policy category: {policy.topic_policy_category}\n"
        f"- Relevance score: {policy.relevance_score}\n"
        f"- Epistemic score: {policy.epistemic_score}\n\n"
        f"{opening_variation}\n\n"
        "Draft response:\n"
        f"{response}"
    )
