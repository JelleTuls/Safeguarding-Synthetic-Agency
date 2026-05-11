import asyncio
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware#

from app.api import chat_router
from app.rate_limits import reset_ip_request_limits

AMSTERDAM = ZoneInfo("Europe/Amsterdam")


async def run_daily():
    while True:
        now = datetime.now(AMSTERDAM)
        next_midnight = (now + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        await asyncio.sleep((next_midnight - now).total_seconds())
        reset_ip_request_limits()


@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(run_daily())
    yield

app = FastAPI(title="Synthetic Social Agent Chat", lifespan=lifespan)

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


app.include_router(chat_router, prefix="/api")
