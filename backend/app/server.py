"""FastAPI application factory for the main SSA backend.

The factory wires CORS, route modules, root redirects, and background lifecycle
tasks. Tests and ASGI servers should import `create_app` rather than assembling
the application manually.
"""

import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.api import chat_router, logs_router, red_team_router
from app.lifecycle import run_daily_rate_limit_reset, warm_guardrail_classifiers
from app.logging.live_logs import install_live_log_capture


FRONTEND_URL = os.getenv("FRONTEND_URL", "http://127.0.0.1:3000")
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    "https://ai-pollster.vercel.app",
    "https://delightful-bay-00709f403.6.azurestaticapps.net",
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(run_daily_rate_limit_reset())
    asyncio.create_task(warm_guardrail_classifiers())
    yield


def create_app() -> FastAPI:
    """Build the FastAPI application and register cross-cutting concerns."""
    install_live_log_capture()
    app = FastAPI(title="Synthetic Social Agent Chat", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/", include_in_schema=False)
    async def root():
        return RedirectResponse(FRONTEND_URL)

    app.include_router(chat_router, prefix="/api")
    app.include_router(logs_router, prefix="/api")
    app.include_router(red_team_router, prefix="/api")
    return app
