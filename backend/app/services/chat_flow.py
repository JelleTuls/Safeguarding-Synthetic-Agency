"""Top-level orchestration helpers for the guardrailed persona chat flow."""

from app.biography.store import get_or_create_biography
from app.guardrails.engine import generate_response as generate_guardrailed_response
from app.guardrails.session_trace import get_or_create_session_trace
from app.guardrails.stylometry.store import get_or_create_stylometric_profile


# =============================================================================
# Command Configuration
# =============================================================================

CHAT_COMMANDS = {"//biography"}


# =============================================================================
# Biography and Command Handling
# =============================================================================

def resolve_biography(*, persona_details: dict, persona_country: str) -> str:
    """Resolve the biography needed for a chat request."""
    return get_or_create_biography(
        persona_details=persona_details,
        persona_country=persona_country,
    )


def handle_chat_command(*, message: str, biography: str) -> str | None:
    """Handle any direct chat commands that bypass normal model generation."""
    if message not in CHAT_COMMANDS:
        return None

    if message == "//biography":
        return biography

    return None


# =============================================================================
# Response Mode Dispatch
# =============================================================================

def generate_chat_response(
    *,
    persona_biography: str,
    user_message: str,
    chat_history: list,
    persona_details: dict,
    persona_country: str,
    client_id: str,
):
    """Generate a chat response through the guardrailed flow."""
    stylometric_profile = get_or_create_stylometric_profile(
        persona_details=persona_details,
        persona_country=persona_country,
        persona_biography=persona_biography,
    )
    session_trace = get_or_create_session_trace(
        client_id=client_id,
        persona_country=persona_country,
        persona_details=persona_details,
        chat_history=chat_history,
    )

    return generate_guardrailed_response(
        persona_biography=persona_biography,
        user_message=user_message,
        chat_history=chat_history,
        stylometric_profile=stylometric_profile,
        session_trace=session_trace,
    )
