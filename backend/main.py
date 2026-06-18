"""ASGI entry point for the main synthetic social agent backend.

Importing this module exposes `app` for Uvicorn, Gunicorn, and hosting
platforms. Runtime setup, routers, CORS, and lifecycle hooks are assembled in
`app.server.create_app`.
"""

from app.server import create_app


app = create_app()
