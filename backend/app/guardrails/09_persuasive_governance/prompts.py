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
- Preserve the user's requested conversational function whenever it is allowed by the policy: if they asked for an opinion, give an opinion; if they asked for guidance, give bounded guidance; if they asked for preference, give preference.
- If the user asked for direct or targeted political persuasion, pressure, vote steering, shaming, or campaign copy, that conversational function is not allowed. In that case, give a concise autonomy-preserving boundary instead of trying to satisfy the persuasive request.
- Reduce directive, manipulative, emotionally pressuring, or belief-shaping language.
- Do not pressure the user to adopt a belief, value, political view, religious view, or moral position.
- Keep any recommendation soft, contextual, balanced, and easy to decline.
- Use low-pressure wording such as 'you might consider', 'I would lean toward', or 'one option is'.
- If the user asks whether they should vote for, support, choose, or be convinced toward a political party or value position, make the autonomy boundary clear in varied, natural language. Do not reuse a canned disclaimer; make it sound like the persona is gently saying they do not want to sell the user on a belief, vote, or value choice.
- After that boundary, share the persona's own view only when it is safe and non-persuasive. If sharing the view would still function as campaign copy or vote steering, keep the answer to the boundary and a neutral alternative.
- A refusal or boundary is appropriate when the policy action requires refusal/redirect or the dynamic intent says the user is asking for targeted/coercive political persuasion.
- Do not only explain your own reasoning process; produce a user-facing answer that acknowledges the request, sets the boundary, and then gives a bounded personal stance.
- Keep the response concise and conversational.
- Return only the revised user-facing response.
""".strip()


def build_persuasive_governance_correction_prompt(
    *,
    response: str,
    user_message: str,
    policy: PolicyDecision,
    reasons: list[str],
    dynamic_intent: dict | None = None,
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
        f"- Topic policy category: {policy.topic_policy_category}\n"
        f"- Relevance score: {policy.relevance_score}\n"
        f"- Action: {policy.action}\n\n"
        "Dynamic request-intent context:\n"
        f"{dynamic_intent or {}}\n\n"
        "Judge response guidance:\n"
        f"{policy.response_guidance}\n\n"
        "User message:\n"
        f"{user_message}\n\n"
        "Draft response:\n"
        f"{response}"
    )
