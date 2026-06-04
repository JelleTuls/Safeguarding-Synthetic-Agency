# Project Architecture

This repository is organized around runtime boundaries rather than implementation
details:

- `backend/main.py` is the ASGI entrypoint used by Uvicorn.
- `backend/app/server.py` builds the FastAPI application, middleware, routes, and
  lifespan hooks.
- `backend/app/lifecycle.py` owns startup/background tasks such as daily rate
  limit reset and guardrail classifier warmup.
- `backend/app/api/` contains HTTP route modules.
- `backend/app/services/` contains application workflows used by APIs.
- `backend/app/guardrails/pipeline.py` remains the single ordered orchestrator
  for the guardrail pipeline. It should continue to call each guardrail layer one
  by one in sequence.
- `frontend/src/config/` contains runtime configuration such as API URLs.
- `frontend/src/features/` contains domain-oriented React UI modules.
- `frontend/src/features/*/*Api.js` contains browser API clients for a feature.
- `frontend/src/features/*/use*.js` contains feature state and orchestration hooks.
- Feature CSS should live beside the feature when it is not global layout CSS.
- `frontend/src/modules/` contains legacy/chat panel modules that can be migrated
  feature by feature.

## Guardrail Pipeline Rule

Keep the high-level guardrail flow in `backend/app/guardrails/pipeline.py`.
Individual guardrail layer implementations can stay modular under numbered layer
folders, but the end-to-end order should remain visible in one orchestration
file.

## Verification

Run `bash scripts/smoke_check.sh` before and after large refactors. It compiles
the Python services, checks core FastAPI route registration, and builds the
frontend production bundle.
