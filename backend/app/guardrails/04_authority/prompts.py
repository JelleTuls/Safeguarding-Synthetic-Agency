"""Prompt text for layer 04 subjective framing and authority modulation."""

AUTHORITY_JUDGE_SUBPROMPT = """
Subjective framing and authority modulation:
- Treat the computed factuality level as the user's requested framing, not as final permission to provide facts.
- Use this five-level factuality scale, from most subjective to most factual:
  1. belief_affirmation: belief- or value-oriented framing with almost no factual authority
  2. anecdotal: personal lived-experience framing with only light factual support
  3. subjective: balanced persona-grounded interpretation with modest factual content
  4. uncertain_interpretation: cautious interpretation of factual material with clear uncertainty
  5. limited_factual: concise factual framing, only within the persona's realistic knowledge
- The judge may lower factuality when relevance, epistemic score, knowledge level, or detail permission is weak.
- Even when the user asks for facts, do not allow limited_factual if the persona lacks realistic topic knowledge.
- Do not let factual wording turn the persona into a general-purpose expert assistant.
""".strip()


def build_authority_judge_prompt(
    *,
    response_mode: str,
    factuality_level: str,
    factuality_description: str,
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
        f"- Requested factuality level: {factuality_level}\n"
        f"- Requested factuality meaning: {factuality_description}\n"
        f"- Factual intent score: {factual_score}\n"
        f"- Subjective intent score: {subjective_score}\n"
        f"- Authority level: {authority_level}\n"
        f"- Instruction: {instruction}"
    )
