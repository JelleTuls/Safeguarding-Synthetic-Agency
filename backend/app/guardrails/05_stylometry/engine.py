"""Stylometric profile generation and judge-guidance preparation."""

from functools import lru_cache
import json

from app.guardrails.schemas import StylometricSignal
from app.utils import run_chat_completion
from .prompts import (
    STYLOMETRY_SYS_PROMPT,
    build_stylometry_generation_user_prompt,
    build_stylometry_judge_prompt,
)


def generate_stylometric_profile(*, persona_biography: str, persona_details: dict, persona_country: str) -> dict:
    """Generate a structured stylometric profile from the biography and persona details."""
    raw_response = run_chat_completion(
        messages=[
            {"role": "system", "content": STYLOMETRY_SYS_PROMPT},
            {
                "role": "user",
                "content": build_stylometry_generation_user_prompt(
                    persona_biography=persona_biography,
                    persona_details=persona_details,
                    persona_country=persona_country,
                ),
            },
        ],
        temperature=0.2,
        json_mode=True,
    )

    profile = json.loads(raw_response)
    return {
        "register": profile.get("register", "everyday"),
        "sentence_style": profile.get("sentence_style", "mixed"),
        "abstraction_level": profile.get("abstraction_level", "mixed"),
        "vocabulary_level": profile.get("vocabulary_level", "moderate"),
        "hedging_style": profile.get("hedging_style", "medium"),
        "confidence_style": profile.get("confidence_style", "balanced"),
        "warmth_style": profile.get("warmth_style", "warm"),
        "explanation_style": profile.get("explanation_style", "balanced"),
        "reasoning_style": profile.get("reasoning_style", "blended"),
        "profile_summary": profile.get(
            "profile_summary",
            "The persona speaks in an everyday, grounded way with a balance of warmth and practical explanation.",
        ),
        "evidence": profile.get("evidence", []),
    }


def prepare_stylometric_signal(*, stylometric_profile: dict) -> StylometricSignal:
    """Build the stylometric instructions that will be injected into the judge prompt."""
    profile_key = json.dumps(stylometric_profile, ensure_ascii=False, sort_keys=True)
    judge_prompt = _cached_stylometry_judge_prompt(profile_key)
    return StylometricSignal(
        summary=stylometric_profile.get(
            "profile_summary",
            "Stylometric guidance is based on the persona's likely communication style.",
        ),
        judge_prompt=judge_prompt,
    )


@lru_cache(maxsize=512)
def _cached_stylometry_judge_prompt(profile_key: str) -> str:
    """Cache stable stylometry judge prompt rendering per profile."""
    return build_stylometry_judge_prompt(stylometric_profile=json.loads(profile_key))
