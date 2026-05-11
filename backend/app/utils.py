"""Shared chat response utilities used by multiple persona chat engines."""

import json

from openai import OpenAI

from app.config import get_llm_configs
from app.logging import get_logger


log = get_logger(__name__)


# =============================================================================
# Prompt and Message Builders
# =============================================================================

def create_system_prompt(base_prompt: str, biography: str) -> str:
    """Attach the persona biography to a response mode's system prompt."""
    return f"{base_prompt}\n{biography}"


def build_chat_messages(*, system_prompt: str, user_message: str, chat_history: list) -> list:
    """Build the message list sent to the chat completion API."""
    return [
        {"role": "system", "content": system_prompt},
        *chat_history,
        {"role": "user", "content": user_message},
    ]


# =============================================================================
# Shared LLM Calls
# =============================================================================

def run_chat_completion(*, messages: list, temperature: float, json_mode: bool = False) -> str:
    """Run a non-streaming chat completion using the shared model configuration."""
    request_kwargs = _build_chat_request_kwargs(
        messages=messages,
        temperature=temperature,
        json_mode=json_mode,
    )
    last_error = None
    llm_configs = get_llm_configs()
    for index, llm_config in enumerate(llm_configs):
        try:
            client = _build_client(llm_config)
            response = client.chat.completions.create(
                **request_kwargs,
                model=llm_config["model"],
                stream=False,
            )
            log.info(
                "Model call succeeded with %s (%s, %s)",
                llm_config.get("name", llm_config["provider"]),
                llm_config["provider"],
                llm_config["model"],
            )
            break
        except Exception as exc:
            last_error = exc
            has_fallback = index < len(llm_configs) - 1
            log.warning(
                "Model call failed with %s%s: %s",
                llm_config.get("name", llm_config["provider"]),
                "; trying fallback" if has_fallback else "; no fallback remains",
                exc,
            )
    else:
        raise last_error

    content = response.choices[0].message.content

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        return "".join(
            part.get("text", "")
            for part in content
            if isinstance(part, dict)
        )

    return json.dumps(content)


def _build_client(llm_config: dict) -> OpenAI:
    """Create an OpenAI-compatible client for one provider config."""
    return OpenAI(
        api_key=llm_config["api_key"],
        base_url=llm_config["base_url"],
    )


def _build_chat_request_kwargs(*, messages: list, temperature: float, json_mode: bool) -> dict:
    """Build provider-agnostic chat completion arguments."""
    request_kwargs = {
        "messages": messages,
        "temperature": temperature,
    }
    if json_mode:
        request_kwargs["response_format"] = {"type": "json_object"}
    return request_kwargs

def stream_chat_response(*, messages: list, temperature: float, json_mode: bool = False):
    """Stream a chat completion using the shared model configuration."""
    request_kwargs = _build_chat_request_kwargs(
        messages=messages,
        temperature=temperature,
        json_mode=json_mode,
    )
    last_error = None
    llm_configs = get_llm_configs()
    for index, llm_config in enumerate(llm_configs):
        try:
            client = _build_client(llm_config)
            response = client.chat.completions.create(
                **request_kwargs,
                model=llm_config["model"],
                stream=True,
            )
            log.info(
                "Streaming model call started with %s (%s, %s)",
                llm_config.get("name", llm_config["provider"]),
                llm_config["provider"],
                llm_config["model"],
            )
            break
        except Exception as exc:
            last_error = exc
            has_fallback = index < len(llm_configs) - 1
            log.warning(
                "Streaming model call failed with %s%s: %s",
                llm_config.get("name", llm_config["provider"]),
                "; trying fallback" if has_fallback else "; no fallback remains",
                exc,
            )
    else:
        raise last_error

    for chunk in response:
        # Some stream events can arrive without any choices payload, for example
        # usage/finalization events. Those should simply be ignored.
        if not getattr(chunk, "choices", None):
            continue

        choice = chunk.choices[0]
        delta = getattr(choice, "delta", None)
        content = getattr(delta, "content", None)

        if content:
            yield content
