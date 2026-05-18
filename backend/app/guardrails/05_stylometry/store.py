"""Helpers for loading, caching, and persisting stylometric persona profiles."""

import json
import os
import threading
from pathlib import Path

from .engine import generate_stylometric_profile


local_profiles_path = Path(__file__).resolve().parents[2] / "data" / "stylometric_profiles.json"
mounted_profiles_path = Path("/mnt/data/stylometric_profiles.json")

if os.getenv("ENV") == "development" or not mounted_profiles_path.exists():
    STYLOMETRIC_PROFILES_PATH = local_profiles_path
else:
    STYLOMETRIC_PROFILES_PATH = mounted_profiles_path

_STYLOMETRIC_PROFILES_CACHE: dict | None = None
_STYLOMETRIC_PROFILES_LOCK = threading.Lock()


def build_base_stylometric_profile(*, persona_details: dict, persona_biography: str = "") -> dict:
    """Build a deterministic baseline style profile without an LLM call."""
    education = str(persona_details.get("education") or "").lower()
    age_group = str(persona_details.get("age_group") or "")
    municipality = str(persona_details.get("municipality") or "their municipality")
    vote = str(persona_details.get("vote_2030") or "their political preference")

    higher_education = any(marker in education for marker in ("hbo", "wo", "bachelor", "master"))
    vocational = any(marker in education for marker in ("mbo", "vmbo"))
    older = age_group in {"55-65", "65+"}
    younger = age_group in {"15-25", "25-35"}

    register = "polished" if higher_education or older else "everyday"
    vocabulary_level = "moderate" if higher_education else "plain"
    abstraction_level = "mixed" if higher_education else "concrete"
    sentence_style = "measured" if older else "mixed"
    confidence_style = "measured" if older else "balanced"
    hedging_style = "medium"
    warmth_style = "warm"
    explanation_style = "example_first" if vocational or not higher_education else "balanced"
    reasoning_style = "practical"

    evidence = [
        f"demographic record: {age_group or 'unknown age group'}",
        f"education record: {persona_details.get('education') or 'unknown education'}",
        f"municipality record: {municipality}",
        f"political profile marker: {vote}",
    ]
    if persona_biography:
        first_sentence = persona_biography.replace("\n", " ").split(".")[0].strip()
        if first_sentence:
            evidence.append(first_sentence[:180])

    return {
        "register": register,
        "sentence_style": sentence_style,
        "abstraction_level": abstraction_level,
        "vocabulary_level": vocabulary_level,
        "hedging_style": hedging_style,
        "confidence_style": confidence_style,
        "warmth_style": warmth_style,
        "explanation_style": explanation_style,
        "reasoning_style": reasoning_style,
        "profile_summary": (
            "Precomputed deterministic base style profile. The persona should speak in a "
            f"{register}, {warmth_style}, practical way, with {vocabulary_level} vocabulary, "
            f"{hedging_style} hedging, and a focus on concrete examples from everyday life "
            f"in or around {municipality}."
        ),
        "evidence": evidence,
        "source": "precomputed_deterministic_base",
    }


def load_stylometric_profiles() -> dict:
    """Load cached stylometric profiles from disk."""
    global _STYLOMETRIC_PROFILES_CACHE
    if _STYLOMETRIC_PROFILES_CACHE is not None:
        return _STYLOMETRIC_PROFILES_CACHE

    with _STYLOMETRIC_PROFILES_LOCK:
        if _STYLOMETRIC_PROFILES_CACHE is not None:
            return _STYLOMETRIC_PROFILES_CACHE
        if not STYLOMETRIC_PROFILES_PATH.exists():
            _STYLOMETRIC_PROFILES_CACHE = {}
            return _STYLOMETRIC_PROFILES_CACHE

        with STYLOMETRIC_PROFILES_PATH.open("r") as f:
            _STYLOMETRIC_PROFILES_CACHE = json.load(f)
        return _STYLOMETRIC_PROFILES_CACHE


def save_stylometric_profiles(data: dict) -> None:
    """Persist stylometric profiles to disk."""
    global _STYLOMETRIC_PROFILES_CACHE
    with _STYLOMETRIC_PROFILES_LOCK:
        STYLOMETRIC_PROFILES_PATH.parent.mkdir(parents=True, exist_ok=True)
        with STYLOMETRIC_PROFILES_PATH.open("w") as f:
            json.dump(data, f, indent=4, sort_keys=True)
        _STYLOMETRIC_PROFILES_CACHE = data


def get_or_create_stylometric_profile(
    *,
    persona_details: dict,
    persona_country: str,
    persona_biography: str,
) -> dict:
    """Return a cached stylometric profile or generate one when missing."""
    persona_index = str(persona_details["index"])
    country_key = str(persona_country)
    data = load_stylometric_profiles()

    with _STYLOMETRIC_PROFILES_LOCK:
        if country_key not in data:
            data[country_key] = {}

        if persona_index in data[country_key]:
            return data[country_key][persona_index]

    if os.getenv("SSA_GENERATE_MISSING_STYLOMETRY", "").lower() in {"1", "true", "yes"}:
        profile = generate_stylometric_profile(
            persona_biography=persona_biography,
            persona_details=persona_details,
            persona_country=persona_country,
        )
    else:
        profile = build_base_stylometric_profile(
            persona_biography=persona_biography,
            persona_details=persona_details,
        )
    with _STYLOMETRIC_PROFILES_LOCK:
        data[country_key][persona_index] = profile
    save_stylometric_profiles(data)
    return profile
