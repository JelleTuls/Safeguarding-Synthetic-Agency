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

    profile = generate_stylometric_profile(
        persona_biography=persona_biography,
        persona_details=persona_details,
        persona_country=persona_country,
    )
    with _STYLOMETRIC_PROFILES_LOCK:
        data[country_key][persona_index] = profile
    save_stylometric_profiles(data)
    return profile
