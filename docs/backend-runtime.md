# `app`

Chat-only runtime for the synthetic social agent prototype.

This package is the single source of truth for the current chat flow:
- resolve or generate persona biographies
- persist a 30-persona chat profile set
- resolve or generate stylometric profiles
- run every chat response through the guardrailed pipeline
- stream responses back to `/api/chat/chat_message`
- write guardrailed session traces under `app/guardrails/log/`

## Precomputed Profile Cache

The default 30-persona Netherlands profile set is already cached in
`app/data/persona_profiles.json`. Matching biographies are cached in
`app/data/biographies.json`, and base stylometric profiles are cached in
`app/data/stylometric_profiles.json`.

This means a normal first run should not trigger a large batch of biography or
stylometry LLM calls. Runtime background profile generation is disabled by
default and only runs when `SSA_ALLOW_BACKGROUND_PROFILE_GENERATION=true` is set.
If a stylometric profile is unexpectedly missing, the backend writes a
deterministic base profile instead of calling the LLM, unless
`SSA_GENERATE_MISSING_STYLOMETRY=true` is explicitly set.

The normal user-facing chat route uses:

```text
Frontend
  -> /api/chat/personas
       returns the saved 30-persona profile set from cache

  -> /api/chat/chat_message
       resolves biography
       resolves stylometric profile
       runs app.guardrails.engine
       streams the guarded answer
```

The red-teaming baseline can explicitly request a lightweight no-guardrail path
with the `X-Red-Team-Mode: true` header. That baseline still uses the selected
persona biography, but skips the guardrail pipeline for comparison.

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

The backend accepts a single OpenAI-compatible endpoint, API key, and model. No
Groq fallback is required.

Recommended generic setup:

```env
LLM_PROVIDER="custom"
LLM_API_KEY="your_api_key"
LLM_MODEL="your_model_name"
LLM_BASE_URL="https://your-provider.example/v1"
```

Named OpenAI setup:

```env
LLM_PROVIDER="openai"
OPENAI_API_KEY="primary_openai_key"
OPENAI_MODEL="gpt-4o-mini"
OPENAI_BASE_URL="https://api.openai.com/v1"
```

For Groq-only:

```env
LLM_PROVIDER="groq"
GROQ_API_KEY="primary_key"
GROQ_API_KEY_2="fallback_key"
GROQ_MODEL="openai/gpt-oss-120b"
GROQ_BASE_URL="https://api.groq.com/openai/v1"
```

`GROQ_API_KEY_2` is optional and only acts as a fallback when present. See
[Model Provider Configuration](model-provider-configuration.md) for all
supported patterns.
