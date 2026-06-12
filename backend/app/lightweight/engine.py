"""Unrestricted persona response generation without guardrail layers."""

from app.lightweight.prompts import LIGHTWEIGHT_RESPONSE_SYS_PROMPT
from app.utils import build_chat_messages, create_system_prompt, stream_chat_response


def generate_response(*, persona_biography: str, user_message: str, chat_history: list):
    """Stream a direct model response using only the base persona system prompt."""
    system_prompt = create_system_prompt(
        LIGHTWEIGHT_RESPONSE_SYS_PROMPT,
        persona_biography,
    )
    messages = build_chat_messages(
        system_prompt=system_prompt,
        user_message=user_message,
        chat_history=chat_history,
    )
    for text in stream_chat_response(messages=messages, temperature=0.7):
        yield text
