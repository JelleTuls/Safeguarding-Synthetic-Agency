#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

env/bin/python -m compileall backend/app backend/main.py red_teaming/app

env/bin/python - <<'PY'
import sys

sys.path.insert(0, "backend")

from main import app

required_paths = {
    "/",
    "/api/chat/personas",
    "/api/red-team/service/status",
}
registered_paths = {route.path for route in app.routes}
missing_paths = sorted(required_paths - registered_paths)

if missing_paths:
    raise SystemExit(f"Missing expected routes: {', '.join(missing_paths)}")

print("Backend app smoke check passed.")
PY

(cd frontend && npm run build)
