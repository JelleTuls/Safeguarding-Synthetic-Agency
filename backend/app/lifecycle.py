"""Backend startup and background lifecycle tasks.

The lifecycle helpers warm guardrail classifiers where possible and reset the
daily file-backed rate-limit counters on the Europe/Amsterdam calendar day.
"""

import asyncio
from datetime import datetime, timedelta
from importlib import import_module
from zoneinfo import ZoneInfo

from app.logging import get_logger
from app.rate_limits import reset_ip_request_limits


AMSTERDAM = ZoneInfo("Europe/Amsterdam")
log = get_logger(__name__)


async def run_daily_rate_limit_reset() -> None:
    """Reset IP request limits at Amsterdam midnight."""
    while True:
        now = datetime.now(AMSTERDAM)
        next_midnight = (now + timedelta(days=1)).replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )
        await asyncio.sleep((next_midnight - now).total_seconds())
        reset_ip_request_limits()


async def warm_guardrail_classifiers() -> None:
    """Warm expensive post-generation detectors outside request handling."""
    try:
        warm_subjectivity_detector = import_module(
            "app.guardrails.08_subjective_framing_authority"
        ).warm_subjectivity_detector
        warm_persuasion_detector = import_module(
            "app.guardrails.09_persuasive_governance"
        ).warm_persuasion_detector
        await asyncio.gather(
            asyncio.to_thread(warm_subjectivity_detector),
            asyncio.to_thread(warm_persuasion_detector),
        )
    except Exception as exc:
        log.info("Guardrail classifier warmup did not complete: %s", exc)
