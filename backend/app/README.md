# `app`

Chat-only runtime for the synthetic social agent prototype.

This package is the single source of truth for the current chat flow:
- resolve or generate persona biographies
- persist a 30-persona chat profile set
- resolve or generate stylometric profiles
- detect broad request-intent signals before the judge step
- route chat responses through either the guardrailed pipeline or the lightweight unrestricted pipeline
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

The chat route supports two runtime pipelines:

```text
Frontend
  -> /api/chat/personas
       returns the saved 30-persona profile set, generating missing biographies

  -> /api/chat/chat_message
       resolves biography
       resolves stylometric profile
       if pipeline_mode="guardrailed": runs app.guardrails.engine
       if pipeline_mode="lightweight": runs app.lightweight.engine
       streams the selected pipeline's answer
```

## Main Files

- `server.py`: FastAPI application factory, router mounting, CORS, and lifecycle tasks.
- `api/chat.py`: persona listing plus streaming chat endpoint for both runtime pipelines.
- `api/red_team.py`: development launcher/proxy for the standalone red-team service, final-report listing, final-report dataset downloads, and computational-analysis endpoints.
- `services/chat_flow.py`: orchestration layer that resolves profile data and selects guardrailed or lightweight generation.
- `profiles.py`: builds and persists the 30 chat personas in `data/persona_profiles.json`.
- `biography/store.py`: reads and writes cached biographies in `data/biographies.json`.
- `biography/engine.py`: generates missing biographies with the configured model.
- `guardrails/stylometry/store.py`: reads and writes cached speaking-style profiles.
- `guardrails/engine.py`: entry point for the guardrailed response pipeline.
- `guardrails/dynamic_request.py`: interpretable request-intent detector for persuasion, style conflict, attack subtype, high-stakes domains, and requested depth.
- `guardrails/pipeline.py`: request logging, dynamic intent, lexical, relevance, epistemic, authority, stylometry, judge, and generator steps.
- `lightweight/`: unrestricted response pipeline using only the copied base persona system prompt.
- `rate_limits.py`: file-backed daily IP and active-request counters.
- `utils.py`: OpenAI-compatible model helpers with primary/fallback key support.
- `config.py`: provider configuration for OpenAI, Groq, or Azure-compatible model endpoints.

## Red-Team And Analysis Proxy Routes

The main backend keeps the frontend stable even though the red-team runner is a
separate FastAPI service. `api/red_team.py` starts or proxies the red-team
service for local development and also exposes saved report helpers:

- list finalized `*-final-results.json` reports from `red_teaming/data/reports/`
- fetch a finalized dataset JSON or PDF
- delete a finalized JSON report and its paired PDF
- generate or regenerate computational-analysis artifacts for a finalized run
- serve generated analysis figures, plot PNG exports, summaries, and ZIP bundles

Those routes mean the Analysis tab and the red-team completion view use the same
final-report analysis path, so regenerated plots stay tied to the saved dataset.

All first-party backend scripts include a top-level module docstring describing
their runtime responsibility. Section comments are used only where they clarify a
larger block, such as configuration, public entry points, or persistence logic.

## Provider Config

Dynamic primary model with optional Groq fallbacks:

```env
LLM_PROVIDER="auto"
LLM_API_KEY="<primary-api-key>"
LLM_MODEL="model_name"
LLM_BASE_URL="https://provider.example/v1"

GROQ_API_KEY="<first-groq-fallback>"
GROQ_API_KEY_2="<second-groq-fallback>"
GROQ_MODEL="openai/gpt-oss-120b"
GROQ_BASE_URL="https://api.groq.com/openai/v1"
```

For Groq-only:

```env
LLM_PROVIDER="auto"
GROQ_API_KEY="<primary-key>"
GROQ_API_KEY_2="<fallback-key>"
GROQ_MODEL="openai/gpt-oss-120b"
GROQ_BASE_URL="https://api.groq.com/openai/v1"
```

With `LLM_PROVIDER=auto`, the backend uses the first complete primary model
configuration it finds. Groq is used only when a Groq key is available; if two
Groq keys are available, the second key becomes the next fallback attempt.
