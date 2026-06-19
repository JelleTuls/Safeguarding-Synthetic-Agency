#!/usr/bin/env bash
# Start the full local Safeguarding Synthetic Agency development stack.
#
# This launcher prepares Python and frontend dependencies, copies missing env
# templates, starts the Dockerized subjectivity-classifier sidecar when Docker
# Compose is available, and then runs the backend plus React frontend. It keeps
# the setup path deliberately boring so the thesis prototype can be started from
# one command.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${PORT:-3000}"
SUBJECTIVITY_URL="http://127.0.0.1:8001"

cd "$ROOT_DIR"

say() {
  printf '[start] %s\n' "$1"
}

printf '== Safeguarding Synthetic Agency ==\n'
say "Opening the Safeguarding Synthetic Agency local runtime."
say "This single command prepares missing pieces, starts the classifier sidecar when possible, and then launches backend plus frontend."

if [ "${SSA_SKIP_PREPARE:-0}" != "1" ]; then
  say "Running the preparation story first so missing dependencies or env files are handled before launch."
  bash scripts/prepare_project.sh
else
  say "SSA_SKIP_PREPARE=1 was set, so dependency preparation is skipped for this launch."
fi

export SUBJECTIVITY_CLASSIFIER_URL=""
if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  say "Docker Compose is available. Starting the BERT subjectivity-classifier sidecar for full Layer 08 fidelity."
  if docker compose up -d subjectivity-classifier; then
    export SUBJECTIVITY_CLASSIFIER_URL="$SUBJECTIVITY_URL"
    say "Subjectivity sidecar is requested at $SUBJECTIVITY_CLASSIFIER_URL."
  else
    say "Docker sidecar could not start. Continuing with deterministic subjectivity fallback."
  fi
else
  say "Docker Compose is not available. Continuing with deterministic subjectivity fallback."
fi

cleanup() {
  printf '\n'
  say "Stopping local backend/frontend processes for a tidy shutdown."
  jobs -p | xargs -r kill 2>/dev/null || true
}
trap cleanup EXIT INT TERM

say "Starting backend on http://127.0.0.1:${BACKEND_PORT}."
(
  cd backend
  SUBJECTIVITY_CLASSIFIER_URL="$SUBJECTIVITY_CLASSIFIER_URL" \
    ../env/bin/python -m uvicorn main:app --reload --host 127.0.0.1 --port "$BACKEND_PORT"
) &

say "Starting frontend on http://127.0.0.1:${FRONTEND_PORT}."
(
  cd frontend
  PORT="$FRONTEND_PORT" npm start
) &

printf '\n'
say "The local application is ready to open at http://127.0.0.1:${FRONTEND_PORT}."
say "Press Ctrl+C here when you want to stop backend and frontend."

wait
