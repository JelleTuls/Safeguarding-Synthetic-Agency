# Synthetic Social Agent Chat

Chat-only prototype for:

Safeguarding Synthetic Agency: A Framework for Measuring and Operationalizing System Integrity in Synthetic Social Agent Systems

The app serves 30 synthetic social agent profiles and opens each profile in a guardrailed chat flow.

## Quick Start

For the easiest local setup, add an LLM API key to `backend/.env` and run:

```bash
./start.sh
```

On the first run, the script will:

- create `backend/.env` from `backend/.env.example` if needed;
- create `frontend/.env` from `frontend/.env.example` if needed;
- create the Python virtual environment in `env/`;
- install backend and red-teaming Python dependencies;
- install frontend dependencies;
- start the Docker subjectivity-classifier sidecar when Docker Compose is available;
- fall back to the built-in deterministic subjectivity scorer when Docker is not available;
- start the backend and frontend.

Open:

```text
http://127.0.0.1:3000
```

The red-teaming service is started from the frontend when you click the
red-teaming button, so it does not need a separate terminal command.

## Subjectivity Classifier Modes

The preferred setup uses the Dockerized `fractalego/subjectivity_classifier`
sidecar on port `8001`. This preserves the BERT/TensorFlow-based classifier path
used by Layer 08.

If Docker is unavailable, the app still starts. Layer 08 automatically uses a
deterministic subjectivity/objectivity fallback scorer with the same output
shape:

- `subjectivity_score`
- `objectivity_score`
- sentence-level labels
- detector source metadata

This fallback keeps the post-generation validation flow active, but it is less
faithful than the Dockerized classifier and should be treated as a development
or sharing fallback rather than the highest-fidelity evaluation mode.

## Manual Run

Backend:

```bash
cd backend
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Frontend:

```bash
cd frontend
npm start
```

The frontend expects `REACT_APP_API_URL` to point at the backend.

## VS Code

Use the `Full Stack: Frontend + Backend` debug compound or the `Start Frontend + Backend` task. The task starts both services and opens the frontend.

## Runtime Shape

- `backend/main.py` exposes the chat API.
- `backend/app/api/chat.py` serves persona profiles and streams chat responses.
- `backend/app/` contains the API, biography generation, profile caching, provider configuration, data files, rate limits, and the guardrailed pipeline.
- `frontend/src/` contains the lightweight chat-only React interface.

## Documentation

- [SSA Guardrail Flow](docs/README.md) shows the simplified thesis-facing flow from user message to final validated response.
