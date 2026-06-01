import asyncio
import os
from importlib import import_module
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware#
from fastapi.responses import RedirectResponse

from app.api import chat_router, red_team_router
from app.logging import get_logger
from app.rate_limits import reset_ip_request_limits

AMSTERDAM = ZoneInfo("Europe/Amsterdam")
log = get_logger(__name__)


async def run_daily():
    while True:
        now = datetime.now(AMSTERDAM)
        next_midnight = (now + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        await asyncio.sleep((next_midnight - now).total_seconds())
        reset_ip_request_limits()


async def warm_guardrail_classifiers():
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(run_daily())
    asyncio.create_task(warm_guardrail_classifiers())
    yield

app = FastAPI(title="Synthetic Social Agent Chat", lifespan=lifespan)
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://127.0.0.1:3000")

origins = [
    "http://localhost:3000",  
    "http://127.0.0.1:3000",
    "https://ai-pollster.vercel.app",
    "https://delightful-bay-00709f403.6.azurestaticapps.net"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, 
    allow_credentials=True,  
    allow_methods=["*"], 
    allow_headers=["*"],
)


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(FRONTEND_URL)


app.include_router(chat_router, prefix="/api")
app.include_router(red_team_router, prefix="/api")
