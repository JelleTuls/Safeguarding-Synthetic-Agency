"""Router exports for the main backend API package.

`app.server` imports these routers and mounts them on the FastAPI application.
Keeping the exports here avoids import-path noise in the server factory.
"""

from app.api.chat import router as chat_router
from app.api.logs import router as logs_router
from app.api.red_team import router as red_team_router

__all__ = ["chat_router", "logs_router", "red_team_router"]
