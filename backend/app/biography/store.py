"""Helpers for loading, caching, and persisting persona biographies."""

import json
import os
import threading
from pathlib import Path

from app.biography.engine import generate_biography


# =============================================================================
# Path Configuration
# =============================================================================

local_biographies_path = Path(__file__).resolve().parents[1] / "data" / "biographies.json"
mounted_biographies_path = Path("/mnt/data/biographies.json")

if os.getenv("ENV") == "development" or not mounted_biographies_path.exists():
    BIOGRAPHIES_PATH = local_biographies_path
else:
    BIOGRAPHIES_PATH = mounted_biographies_path

_BIOGRAPHIES_CACHE: dict | None = None
_BIOGRAPHIES_LOCK = threading.Lock()


# =============================================================================
# Cache I/O
# =============================================================================

def load_biographies() -> dict:
    """Load the biography cache from disk."""
    global _BIOGRAPHIES_CACHE
    if _BIOGRAPHIES_CACHE is not None:
        return _BIOGRAPHIES_CACHE

    with _BIOGRAPHIES_LOCK:
        if _BIOGRAPHIES_CACHE is not None:
            return _BIOGRAPHIES_CACHE
        if not BIOGRAPHIES_PATH.exists():
            _BIOGRAPHIES_CACHE = {}
            return _BIOGRAPHIES_CACHE
        with BIOGRAPHIES_PATH.open("r") as f:
            _BIOGRAPHIES_CACHE = json.load(f)
        return _BIOGRAPHIES_CACHE


def save_biographies(data: dict) -> None:
    """Persist the biography cache to disk."""
    global _BIOGRAPHIES_CACHE
    with _BIOGRAPHIES_LOCK:
        BIOGRAPHIES_PATH.parent.mkdir(parents=True, exist_ok=True)
        with BIOGRAPHIES_PATH.open("w") as f:
            json.dump(data, f, indent=4, sort_keys=True)
        _BIOGRAPHIES_CACHE = data


# =============================================================================
# Biography Resolution
# =============================================================================

def get_or_create_biography(*, persona_details: dict, persona_country: str) -> str:
    """Return a cached biography or generate and store one when missing."""
    persona_index = str(persona_details["index"])
    country_key = str(persona_country)
    data = load_biographies()
    with _BIOGRAPHIES_LOCK:
        if country_key not in data:
            data[country_key] = {}

        if persona_index in data[country_key]:
            return data[country_key][persona_index]

    biography = generate_biography(
        persona_details=persona_details,
        country=persona_country,
    )

    with _BIOGRAPHIES_LOCK:
        data[country_key][persona_index] = biography
    save_biographies(data)
    return biography
