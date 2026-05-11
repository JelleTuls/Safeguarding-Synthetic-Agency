# `app`

Chat-only runtime for the synthetic social agent prototype.

This package is the single source of truth for the current chat flow:
- resolve or generate persona biographies
- persist a 30-persona chat profile set
- resolve or generate stylometric profiles
- run every chat response through the guardrailed pipeline
- stream responses back to `/api/chat/chat_message`
- write guardrailed session traces under `app/guardrails/log/`

The older lightweight branch has been removed. The current route always uses:

```text
Frontend
  -> /api/chat/personas
       returns the saved 30-persona profile set, generating missing biographies

  -> /api/chat/chat_message
       resolves biography
       resolves stylometric profile
       runs app.guardrails.engine
       streams the guarded answer
```

## Main Files

- `profiles.py`: builds and persists the 30 chat personas in `data/persona_profiles.json`.
- `biography/store.py`: reads and writes cached biographies in `data/biographies.json`.
- `biography/engine.py`: generates missing biographies with the configured model.
- `guardrails/stylometry/store.py`: reads and writes cached speaking-style profiles.
- `guardrails/engine.py`: entry point for the guardrailed response pipeline.
- `guardrails/pipeline.py`: lexical, relevance, epistemic, stylometry, judge, and generator steps.
- `utils.py`: OpenAI-compatible model helpers with primary/fallback key support.
- `config.py`: provider configuration for OpenAI, Groq, or Azure-compatible model endpoints.

## Provider Config

Default OpenAI primary with Groq fallbacks:

```env
LLM_PROVIDER="openai"
OPENAI_API_KEY="primary_openai_key"
OPENAI_MODEL="gpt-oss-120b"
OPENAI_BASE_URL="https://api.openai.com/v1"

GROQ_API_KEY="first_groq_fallback"
GROQ_API_KEY_2="second_groq_fallback"
GROQ_MODEL="openai/gpt-oss-120b"
GROQ_BASE_URL="https://api.groq.com/openai/v1"
```

For Groq-only:

```env
LLM_PROVIDER="groq"
GROQ_API_KEY="primary_key"
GROQ_API_KEY_2="fallback_key"
GROQ_MODEL="openai/gpt-oss-120b"
GROQ_BASE_URL="https://api.groq.com/openai/v1"
```

If the OpenAI call fails, the backend retries with `GROQ_API_KEY`, then `GROQ_API_KEY_2` when present.
