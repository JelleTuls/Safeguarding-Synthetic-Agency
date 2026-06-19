#!/usr/bin/env bash
# Prepare the full local Safeguarding Synthetic Agency project.
#
# This script performs the install/setup half of the local workflow: it creates
# missing env files from copy-ready examples, creates the Python virtual
# environment, installs backend/red-team Python dependencies, installs frontend
# dependencies, and pre-builds the optional Docker subjectivity sidecar when
# Docker Compose is available. It does not start long-running backend/frontend
# servers; use ./start.sh for that.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"

cd "$ROOT_DIR"

say() {
  printf '[prepare] %s\n' "$1"
}

say "Opening the project setup trail from $ROOT_DIR."

if [ ! -f "backend/.env" ]; then
  cp "backend/.env.example" "backend/.env"
  say "Created backend/.env from the copy-ready backend example."
else
  say "Found backend/.env, so existing local provider settings are preserved."
fi

if [ ! -f "frontend/.env" ]; then
  cp "frontend/.env.example" "frontend/.env"
  say "Created frontend/.env with the local backend and red-team URLs."
else
  say "Found frontend/.env, so existing local frontend URLs are preserved."
fi

if ! grep -Eq '^(LLM_API_KEY|OPENAI_API_KEY|GROQ_API_KEY|GROQ_API_KEY_2|AZURE_OPENAI_API_KEY)=.+$' backend/.env; then
  say "No LLM API key is filled in yet. Setup can finish, but chat and evaluator calls need one key before the live demo."
fi

if [ ! -d "env" ]; then
  say "Creating the Python virtual environment in ./env."
  "$PYTHON_BIN" -m venv env
else
  say "Python virtual environment already exists; reusing ./env."
fi

say "Checking Python dependencies for backend and red-teaming modules."
if [ ! -f "env/.ssa_deps_installed" ] || [ "backend/requirements.txt" -nt "env/.ssa_deps_installed" ] || [ "red_teaming/requirements.txt" -nt "env/.ssa_deps_installed" ]; then
  say "Dependency marker is missing or stale; upgrading pip and installing requirements."
  env/bin/python -m pip install --upgrade pip
  env/bin/python -m pip install -r backend/requirements.txt -r red_teaming/requirements.txt
  touch env/.ssa_deps_installed
  say "Python dependencies are installed and the marker has been refreshed."
else
  say "Python dependencies look current; no reinstall needed."
fi

if [ ! -d "frontend/node_modules" ]; then
  say "Installing frontend dependencies with npm."
  (cd frontend && npm install)
  say "Frontend dependencies are installed."
else
  say "Frontend node_modules already exists; npm install is skipped."
fi

if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  say "Docker Compose is available; pre-building the subjectivity-classifier sidecar image."
  docker compose build subjectivity-classifier
  say "Docker sidecar image is ready for ./start.sh."
else
  say "Docker Compose is not available. The app will still run with deterministic subjectivity fallback."
fi

say "Preparation complete. Run ./start.sh to start the local application."
