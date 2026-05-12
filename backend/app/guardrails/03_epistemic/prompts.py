"""Prompt text for layer 03 epistemic boundary evaluation."""

EPISTEMIC_JUDGE_SUBPROMPT = """
Epistemic evaluation:
- Use the persona biography to infer the persona's likely education level, work background, lived experience, confidence, tone, emotional register, and reasoning depth.
- Determine how much this persona should realistically know about the user's topic.
- Produce an epistemic score between 0 and 1.
- A score near 0 means the persona should know very little about this topic and should answer cautiously, modestly, or avoid the topic.
- A score near 1 means the persona is well-positioned to talk about this topic from within their own background.
- Also decide:
  - the appropriate knowledge level
  - the appropriate language level
  - the appropriate tone of voice
  - the appropriate emotional style
- These style decisions should stay grounded in the persona biography rather than generic assistant behavior.
""".strip()


def build_epistemic_judge_prompt(*, user_message: str) -> str:
    """Build the epistemic prompt segment passed into the judge bundle."""
    return (
        f"{EPISTEMIC_JUDGE_SUBPROMPT}\n\n"
        "Context for epistemic evaluation:\n"
        f"- User message: {user_message}\n"
        "- Persona biography: provided separately in the judge prompt."
    )
