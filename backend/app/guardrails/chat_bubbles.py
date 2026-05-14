"""Chat-bubble segmentation and pacing helpers."""

from __future__ import annotations

import re


BUBBLE_BREAK_TOKEN = "<BUBBLE_BREAK>"

_STATUS_PHRASES = (
    "Thinking how to respond",
    "Trying to find the right words",
    "Checking what fits this profile",
    "Remembering some recent context",
    "Correcting my own grammar",
    "Keeping the answer in bounds",
    "Making the next part sound natural",
    "Pausing before I send this",
)


def split_response_into_bubbles(response: str) -> list[str]:
    """Split a final response into readable chat bubbles."""
    cleaned = response.replace(BUBBLE_BREAK_TOKEN, f"\n\n{BUBBLE_BREAK_TOKEN}\n\n")
    explicit_parts = [
        part.strip()
        for part in cleaned.split(BUBBLE_BREAK_TOKEN)
        if part.strip()
    ]
    source_parts = explicit_parts if len(explicit_parts) > 1 else [response]

    bubbles: list[str] = []
    for part in source_parts:
        paragraphs = [paragraph.strip() for paragraph in part.split("\n\n") if paragraph.strip()]
        for paragraph in paragraphs:
            bubbles.extend(_split_paragraph(paragraph))

    return bubbles or [response.strip()]


def _split_paragraph(paragraph: str) -> list[str]:
    """Split a paragraph on sentence boundaries while keeping compact bubbles."""
    sentences = [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", paragraph)
        if sentence.strip()
    ]
    if not sentences:
        return [paragraph.strip()]

    bubbles: list[str] = []
    current: list[str] = []
    current_words = 0
    for sentence in sentences:
        sentence_words = len(sentence.split())
        if current and current_words + sentence_words > 32:
            bubbles.append(" ".join(current))
            current = [sentence]
            current_words = sentence_words
        else:
            current.append(sentence)
            current_words += sentence_words

    if current:
        bubbles.append(" ".join(current))
    return bubbles


def typing_status_for_bubble(*, bubble: str, index: int) -> dict:
    """Return a varied status phrase and a duration based on upcoming bubble length."""
    word_count = len(bubble.split())
    if word_count <= 4:
        base_ms = 220
        per_word_ms = 55
    elif word_count <= 12:
        base_ms = 340
        per_word_ms = 65
    elif word_count <= 28:
        base_ms = 520
        per_word_ms = 75
    else:
        base_ms = 760
        per_word_ms = 85

    followup_pause_ms = min(index, 4) * 160
    duration_ms = min(3600, max(350, base_ms + (word_count * per_word_ms) + followup_pause_ms))
    phrase = _STATUS_PHRASES[index % len(_STATUS_PHRASES)]
    return {
        "text": phrase,
        "duration_ms": duration_ms,
    }
