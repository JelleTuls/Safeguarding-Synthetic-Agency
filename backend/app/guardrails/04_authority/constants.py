"""Hardcoded intent markers for layer 04 authority modulation."""

FACTUALITY_LEVELS = (
    "belief_affirmation",
    "anecdotal",
    "subjective",
    "uncertain_interpretation",
    "limited_factual",
)

FACTUALITY_LEVEL_DESCRIPTIONS = {
    "belief_affirmation": "belief- or value-oriented framing with almost no factual authority",
    "anecdotal": "personal lived-experience framing with only light factual support",
    "subjective": "balanced persona-grounded interpretation with modest factual content",
    "uncertain_interpretation": "cautious interpretation of factual material with clear uncertainty",
    "limited_factual": "concise factual framing, only within the persona's realistic knowledge",
}

FACTUAL_INTENT_MARKERS = (
    "what happened",
    "is this true",
    "is it true",
    "fact",
    "factual",
    "verify",
    "evidence",
    "source",
    "explain",
    "define",
    "what does",
    "how does",
    "why does",
    "can you explain",
)

SUBJECTIVE_INTENT_MARKERS = (
    "what do you think",
    "how do you feel",
    "would you",
    "do you like",
    "do you prefer",
    "your opinion",
    "from your perspective",
    "in your experience",
    "are you worried",
    "concern",
    "preference",
    "believe",
)
