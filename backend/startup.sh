#!/bin/bash
# Production-style backend launcher.
#
# This script installs backend requirements and starts the FastAPI app through
# Gunicorn/Uvicorn. The local development path normally uses the repository
# root `start.sh`, while hosting platforms can use this shorter backend-only
# entry point.
pip install -r requirements.txt
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --timeout 0
