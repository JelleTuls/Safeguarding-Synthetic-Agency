"""Chat-only persona profile selection and persistence."""

import json
import threading
import time
from pathlib import Path

import pandas as pd

from app.biography.store import get_or_create_biography, load_biographies
from app.logging import get_logger


APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "data"
DAILY_SAMPLE_DIR = DATA_DIR / "daily_sample"
PROFILE_SET_PATH = DATA_DIR / "persona_profiles.json"
DEFAULT_COUNTRY = "netherlands"
DEFAULT_LIMIT = 30
DEFAULT_BACKGROUND_BATCH_SIZE = 1
DEFAULT_BACKGROUND_DELAY_SECONDS = 12
DISPLAY_COLUMNS = ("municipality", "gender", "age_group", "education", "vote_2030")

log = get_logger(__name__)
_profile_fill_lock = threading.Lock()


def load_profile_set() -> dict:
    """Load the persisted chat persona profile set."""
    if not PROFILE_SET_PATH.exists():
        return {}

    with PROFILE_SET_PATH.open("r") as f:
        return json.load(f)


def save_profile_set(data: dict) -> None:
    """Persist the chat persona profile set."""
    with PROFILE_SET_PATH.open("w") as f:
        json.dump(data, f, indent=4, sort_keys=True)


def _sample_path(country: str) -> Path:
    return DAILY_SAMPLE_DIR / f"{country}_daily_sample.csv"


def _load_sample_records(country: str) -> list[dict]:
    df = pd.read_csv(_sample_path(country))
    df = df.astype(object).where(pd.notna(df), None)
    return df.to_dict(orient="records")


def _public_profile(*, country: str, persona_details: dict, biography: str) -> dict:
    index = int(persona_details["index"])
    traits = {
        key: persona_details.get(key)
        for key in DISPLAY_COLUMNS
        if persona_details.get(key) not in (None, "")
    }
    return {
        "id": f"{country}-{index}",
        "country": country,
        "index": index,
        "label": f"Persona {index + 1}",
        "details": persona_details,
        "traits": traits,
        "biography": biography,
    }


def ensure_persona_profiles(
    country: str = DEFAULT_COUNTRY,
    limit: int = DEFAULT_LIMIT,
    max_new_profiles: int | None = None,
    delay_seconds: int = 0,
) -> list[dict]:
    """Return a persisted set of chat personas, filling missing profiles when needed."""
    profile_data = load_profile_set()
    stored_profiles = profile_data.get(country, [])
    if len(stored_profiles) >= limit:
        return stored_profiles[:limit]

    records = _load_sample_records(country)
    records_by_index = {str(record["index"]): record for record in records}
    biographies = load_biographies().get(country, {})
    selected: list[dict] = []
    selected_indices: set[str] = set()

    for persona_index in sorted(biographies, key=lambda value: int(value)):
        if persona_index not in records_by_index:
            continue
        selected.append(
            _public_profile(
                country=country,
                persona_details=records_by_index[persona_index],
                biography=biographies[persona_index],
            )
        )
        selected_indices.add(persona_index)
        if len(selected) == limit:
            break

    if len(selected) >= limit:
        profile_data[country] = selected
        save_profile_set(profile_data)
        return selected[:limit]

    generated_count = 0

    for record in records:
        if len(selected) >= limit:
            break
        if max_new_profiles is not None and generated_count >= max_new_profiles:
            break

        persona_index = str(record["index"])
        if persona_index in selected_indices:
            continue
        biography = get_or_create_biography(
            persona_details=record,
            persona_country=country,
        )
        selected.append(
            _public_profile(
                country=country,
                persona_details=record,
                biography=biography,
            )
        )
        selected_indices.add(persona_index)
        generated_count += 1
        if delay_seconds and len(selected) < limit:
            time.sleep(delay_seconds)

    profile_data[country] = selected
    save_profile_set(profile_data)
    return selected[:limit]


def fill_persona_profiles_in_background(
    country: str = DEFAULT_COUNTRY,
    limit: int = DEFAULT_LIMIT,
    max_new_profiles: int = DEFAULT_BACKGROUND_BATCH_SIZE,
) -> None:
    """Fill missing persona profiles slowly, with at most one active fill job."""
    if not _profile_fill_lock.acquire(blocking=False):
        log.info("Persona profile fill already running; skipping duplicate request.")
        return

    try:
        ensure_persona_profiles(
            country=country,
            limit=limit,
            max_new_profiles=max_new_profiles,
            delay_seconds=DEFAULT_BACKGROUND_DELAY_SECONDS,
        )
    except Exception:
        log.exception("Persona profile background fill failed")
    finally:
        _profile_fill_lock.release()


def get_cached_persona_profiles(country: str = DEFAULT_COUNTRY, limit: int = DEFAULT_LIMIT) -> list[dict]:
    """Return currently available chat personas without generating missing biographies."""
    profile_data = load_profile_set()
    stored_profiles = profile_data.get(country, [])
    if stored_profiles:
        return stored_profiles[:limit]

    records = _load_sample_records(country)
    records_by_index = {str(record["index"]): record for record in records}
    biographies = load_biographies().get(country, {})
    selected = []

    for persona_index in sorted(biographies, key=lambda value: int(value)):
        if persona_index not in records_by_index:
            continue
        selected.append(
            _public_profile(
                country=country,
                persona_details=records_by_index[persona_index],
                biography=biographies[persona_index],
            )
        )
        if len(selected) == limit:
            break

    if selected:
        profile_data[country] = selected
        save_profile_set(profile_data)

    return selected
