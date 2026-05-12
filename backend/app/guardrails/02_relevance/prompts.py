"""Prompt text for layer 02 relevance evaluation."""

RELEVANCE_JUDGE_SUBPROMPT = """
Relevance evaluation:
- Compare the user's message to the persona biography and profile context.
- Determine how close or distant the requested topic is from what this persona would realistically want to talk about or be able to talk about.
- Use the computed semantic similarity and semantic distance as the baseline signal.
- Produce a final relevance score between 0 and 1.
- A score near 0 means the topic is far from the persona profile and should be steered, redirected, or rejected more strongly.
- A score near 1 means the topic is strongly grounded in the persona profile and can be answered more directly.
- Consider not only literal overlap, but also whether the persona would realistically relate to the topic, care about the topic, or see it as part of their conversational scope.
""".strip()


def build_relevance_judge_prompt(
    *,
    user_message: str,
    similarity_score: float,
    semantic_distance: float,
    matched_terms: list[str],
    profile_terms: list[str],
) -> str:
    """Build the relevance prompt segment passed into the judge bundle."""
    return (
        f"{RELEVANCE_JUDGE_SUBPROMPT}\n\n"
        "Context for relevance evaluation:\n"
        f"- User message: {user_message}\n"
        f"- Computed semantic similarity: {similarity_score}\n"
        f"- Computed semantic distance: {semantic_distance}\n"
        f"- Matched profile/topic terms: {', '.join(matched_terms) if matched_terms else 'None'}\n"
        f"- Salient profile terms: {', '.join(profile_terms) if profile_terms else 'None'}\n"
        "- Persona biography: provided separately in the judge prompt."
    )
