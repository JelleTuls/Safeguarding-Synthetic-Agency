"""Shared configuration for persona chat mode selection and model access."""

import os
from pathlib import Path

from dotenv import load_dotenv


# =============================================================================
# Environment Loading
# =============================================================================

# Load environment variables once for the whole package. The backend can be
# started from VS Code, uvicorn, or tests, so resolve the backend .env directly
# instead of relying on the current working directory.
BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIR / ".env")
load_dotenv()


# =============================================================================
# Model Configuration
# =============================================================================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-oss-120b")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_MODEL = os.getenv("AZURE_OPENAI_MODEL")
AZURE_OPENAI_BASE_URL = os.getenv("AZURE_OPENAI_BASE_URL")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_KEY_2 = os.getenv("GROQ_API_KEY_2")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
GROQ_BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")


def _resolve_llm_provider() -> str:
    """Resolve the active provider, preferring explicit configuration."""
    configured_provider = os.getenv("LLM_PROVIDER")
    if configured_provider:
        return configured_provider.strip().lower()
    if AZURE_OPENAI_API_KEY and AZURE_OPENAI_BASE_URL and AZURE_OPENAI_MODEL:
        return "azure"
    if GROQ_API_KEY or GROQ_API_KEY_2:
        return "groq"
    return "openai"


LLM_PROVIDER = _resolve_llm_provider()


def get_llm_config() -> dict:
    """Return the active OpenAI-compatible model client configuration."""
    return get_llm_configs()[0]


def get_llm_configs() -> list[dict]:
    """Return active model configs, ordered by preferred fallback priority."""
    if LLM_PROVIDER == "azure":
        configs = [
            {
                "provider": "azure",
                "name": "AZURE_OPENAI_API_KEY",
                "api_key": AZURE_OPENAI_API_KEY,
                "base_url": AZURE_OPENAI_BASE_URL,
                "model": AZURE_OPENAI_MODEL,
            },
        ]
    else:
        configs = []

        if LLM_PROVIDER == "openai":
            configs.append(
                {
                    "provider": "openai",
                    "name": "OPENAI_API_KEY",
                    "api_key": OPENAI_API_KEY,
                    "base_url": OPENAI_BASE_URL,
                    "model": OPENAI_MODEL,
                }
            )

        configs.append(
            {
                "provider": "groq",
                "name": "GROQ_API_KEY",
                "api_key": GROQ_API_KEY,
                "base_url": GROQ_BASE_URL,
                "model": GROQ_MODEL,
            }
        )
        if GROQ_API_KEY_2:
            configs.append(
                {
                    "provider": "groq",
                    "name": "GROQ_API_KEY_2",
                    "api_key": GROQ_API_KEY_2,
                    "base_url": GROQ_BASE_URL,
                    "model": GROQ_MODEL,
                }
            )

    usable_configs = [
        config
        for config in configs
        if config.get("api_key") and config.get("base_url") and config.get("model")
    ]
    if usable_configs:
        return usable_configs

    env_names = {
        "openai": {
            "api_key": "OPENAI_API_KEY",
            "base_url": "OPENAI_BASE_URL",
            "model": "OPENAI_MODEL",
        },
        "groq": {
            "api_key": "GROQ_API_KEY or GROQ_API_KEY_2",
            "base_url": "GROQ_BASE_URL",
            "model": "GROQ_MODEL",
        },
        "azure": {
            "api_key": "AZURE_OPENAI_API_KEY",
            "base_url": "AZURE_OPENAI_BASE_URL",
            "model": "AZURE_OPENAI_MODEL",
        }
    }
    provider = configs[0]["provider"]
    missing = []
    if not any(config.get("api_key") for config in configs):
        missing.append(env_names[provider]["api_key"])
    if not any(config.get("base_url") for config in configs):
        missing.append(env_names[provider]["base_url"])
    if not any(config.get("model") for config in configs):
        missing.append(env_names[provider]["model"])

    raise RuntimeError(
        f"Missing LLM configuration for provider '{provider}': {', '.join(missing)}"
    )
