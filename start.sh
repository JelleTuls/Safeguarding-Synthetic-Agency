#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${PORT:-3000}"
SUBJECTIVITY_URL="http://127.0.0.1:8001"

cd "$ROOT_DIR"

echo "== Safeguarding Synthetic Agency =="

if [ ! -f "backend/.env" ]; then
  cp "backend/.env.example" "backend/.env"
  echo "Created backend/.env from backend/.env.example."
  echo "Add at least one LLM API key to backend/.env, then run ./start.sh again."
  exit 1
fi

if ! grep -Eq '^(LLM_API_KEY|OPENAI_API_KEY|GROQ_API_KEY|GROQ_API_KEY_2|AZURE_OPENAI_API_KEY)=.+$' backend/.env; then
  echo "backend/.env does not appear to contain an LLM API key."
  echo "Add one provider key, then run ./start.sh again."
  exit 1
fi

if [ ! -f "frontend/.env" ]; then
  cp "frontend/.env.example" "frontend/.env"
  echo "Created frontend/.env from frontend/.env.example."
fi

if [ ! -d "env" ]; then
  echo "Creating Python virtual environment in ./env ..."
  "$PYTHON_BIN" -m venv env
fi

echo "Installing Python dependencies from backend/requirements.txt and red_teaming/requirements.txt when needed ..."
if [ ! -f "env/.ssa_deps_installed" ] || [ "backend/requirements.txt" -nt "env/.ssa_deps_installed" ] || [ "red_teaming/requirements.txt" -nt "env/.ssa_deps_installed" ]; then
  env/bin/python -m pip install --upgrade pip
  env/bin/python -m pip install -r backend/requirements.txt -r red_teaming/requirements.txt
  touch env/.ssa_deps_installed
fi

echo "Installing frontend dependencies when needed ..."
if [ ! -d "frontend/node_modules" ]; then
  (cd frontend && npm install)
fi

export SUBJECTIVITY_CLASSIFIER_URL=""
if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  echo "Docker detected. Starting BERT subjectivity-classifier sidecar ..."
  if docker compose up -d subjectivity-classifier; then
    export SUBJECTIVITY_CLASSIFIER_URL="$SUBJECTIVITY_URL"
    echo "Subjectivity sidecar requested at $SUBJECTIVITY_CLASSIFIER_URL."
  else
    echo "Docker sidecar could not start. Continuing with deterministic subjectivity fallback."
  fi
else
  echo "Docker Compose not available. Continuing with deterministic subjectivity fallback."
fi

cleanup() {
  echo ""
  echo "Stopping local backend/frontend processes ..."
  jobs -p | xargs -r kill 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "Starting backend on http://127.0.0.1:${BACKEND_PORT}"
(
  cd backend
  SUBJECTIVITY_CLASSIFIER_URL="$SUBJECTIVITY_CLASSIFIER_URL" \
    ../env/bin/python -m uvicorn main:app --reload --host 127.0.0.1 --port "$BACKEND_PORT"
) &

echo "Starting frontend on http://127.0.0.1:${FRONTEND_PORT}"
(
  cd frontend
  PORT="$FRONTEND_PORT" npm start
) &

echo ""
echo "Open the app at http://127.0.0.1:${FRONTEND_PORT}"
echo "Press Ctrl+C to stop backend and frontend."

wait -n
