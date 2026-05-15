# Synthetic Social Agent Chat

Chat-only prototype for:

Safeguarding Synthetic Agency: A Framework for Measuring and Operationalizing System Integrity in Synthetic Social Agent Systems

The app serves 30 synthetic social agent profiles and opens each profile in a guardrailed chat flow.

## Run Locally

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
