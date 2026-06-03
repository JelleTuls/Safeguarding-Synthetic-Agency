# Safeguarding Synthetic Social Agents

### Chat-only prototype for:

Safeguarding Synthetic Agency: A Framework for Measuring and Operationalizing System Integrity in Synthetic Social Agent Systems

The app serves 30 synthetic social agent profiles and opens each profile in a guardrailed chat flow.

> [!IMPORTANT]
> **Full guardrail fidelity requires Docker to be installed and running.**
>
> Layer 08 uses a Dockerized `fractalego/subjectivity_classifier` sidecar for the
> BERT/TensorFlow-based subjectivity classifier. For the full framework, install
> Docker Desktop and keep it open before running the project.
>
> If Docker is missing, closed, or unable to start the sidecar, the project still
> runs in fallback mode. In fallback mode, Layer 08 uses the built-in
> deterministic subjectivity/objectivity scorer. This keeps the app usable and
> the guardrail flow active, but it is **not the highest-fidelity classifier
> mode**.

## Docker Requirement

Install Docker Desktop for your operating system:

- **macOS:** https://docs.docker.com/desktop/setup/install/mac-install/
- **Windows:** https://docs.docker.com/desktop/setup/install/windows-install/
- **Linux:** https://docs.docker.com/desktop/setup/install/linux/

After installation:

1. Open Docker Desktop.
2. Wait until Docker says it is running.
3. Start this project with `./start.sh`.

No separate manual installation step is required for the subjectivity classifier.
On first run, `./start.sh` asks Docker Compose to build and start the
`subjectivity-classifier` sidecar from `services/subjectivity_classifier/`.
That Docker image installs the classifier's legacy TensorFlow dependencies
inside the container.

Optional higher-quality embedding step: for the best classifier quality, place
the full Stanford GloVe 6B 50d file here before starting the project:

```text
services/subjectivity_classifier/model/glove.6B.50d.txt
```

If this file is missing, the Docker sidecar still starts with compact
development embeddings, so this is optional rather than required.

You can quickly check whether Docker is available with:

```bash
docker compose version
```

If that command fails, the project will fall back to deterministic subjectivity
scoring.

## Quick Start

For the easiest local setup, make sure Docker Desktop is open and running, then
run:

```bash
./start.sh
```

On the first run, the script will:

- create `backend/.env` from `backend/.env.example` if needed;
- create `frontend/.env` from `frontend/.env.example` if needed;
- create the Python virtual environment in `env/`;
- install all required backend Python packages from `backend/requirements.txt`;
- install all required red-teaming Python packages from `red_teaming/requirements.txt`;
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

Chat and evaluator calls still need one usable LLM provider in `backend/.env`.
If no key is configured yet, the project still starts so the frontend/backend
stack can be checked, but model-backed interactions will show a configuration
error until a provider key is added.

## Setting Up an API Key

The full chat and red-teaming evaluator flows require at least one usable LLM
configuration in `backend/.env`. Keep `LLM_PROVIDER=auto` unless you specifically
want to force one provider.

For most users, the rule is simple: **choose one setup block, fill in only that
block, and leave the other API-key fields empty.** The system will use whichever
complete block it finds.

The easiest and most flexible block is the generic OpenAI-compatible block:

- `LLM_API_KEY`: your provider API key
- `LLM_MODEL`: the model name your provider tells you to use
- `LLM_BASE_URL`: the provider's OpenAI-compatible API URL

This generic block is tried first because it works with many providers, including
institutional gateways and local OpenAI-compatible servers.

The named provider blocks are there for convenience:

- Azure users can fill `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_MODEL`, and
  `AZURE_OPENAI_BASE_URL`.
- OpenAI users can fill `OPENAI_API_KEY`, `OPENAI_MODEL`, and
  `OPENAI_BASE_URL`.
- Groq users can fill `GROQ_API_KEY`, `GROQ_MODEL`, and `GROQ_BASE_URL`.

`GROQ_API_KEY_2` is optional. It is only used as an extra fallback if the first
Groq key fails or reaches a limit.

In short:

- If you only fill the generic `LLM_*` block, the system uses that.
- If you only fill the Groq block, the system uses Groq.
- If you fill the generic block and Groq, the system tries the generic endpoint
  first and Groq only as fallback.
- If no complete block is filled, the backend cannot call an AI model and will
  show a configuration error.

### Normal OpenAI-Compatible Endpoint

Use this option when you have one normal provider endpoint, model name, and API
key. This can be OpenAI, an institutional gateway, a local OpenAI-compatible
server, or another provider exposing `/chat/completions`.

```env
LLM_PROVIDER=auto
LLM_API_KEY=your_api_key
LLM_MODEL=your_model_name
LLM_BASE_URL=https://your-provider.example/v1
```

The backend uses the model name you provide. See
[Model Provider Configuration](docs/model-provider-configuration.md) for OpenAI,
Groq, Azure, and custom OpenAI-compatible examples.

### Groq Setup

Groq is a convenient testing provider because it exposes an OpenAI-compatible
chat-completions endpoint and usually takes only a few minutes to set up. The
official Groq quickstart says to create an API key in the Groq Console and use
it as `GROQ_API_KEY`: https://console.groq.com/docs/quickstart

To create a Groq key:

1. Go to https://console.groq.com.
2. Create an account or sign in.
3. Open the API keys page: https://console.groq.com/keys.
4. Click **Create API Key**.
5. Copy the key once. Treat it like a password; do not commit it to git.
6. Open `backend/.env` and fill in:

```env
LLM_PROVIDER=auto
GROQ_API_KEY=your_groq_api_key
GROQ_API_KEY_2=
GROQ_MODEL=openai/gpt-oss-120b
GROQ_BASE_URL=https://api.groq.com/openai/v1
```

For testing, one Groq key is enough. If you add `GROQ_API_KEY_2`, the backend
uses it as a second Groq fallback route.

## Dependencies and Cached Profiles

The Python dependency installation is handled automatically by `./start.sh`.
If either `backend/requirements.txt` or `red_teaming/requirements.txt` changes,
the launcher reinstalls the Python packages on the next run.

The 30 default persona profiles, biographies, and base stylometric profiles are
already cached in `backend/app/data/`. Normal first use should not trigger a
large profile-generation batch. Runtime background profile generation is off by
default and only runs when `SSA_ALLOW_BACKGROUND_PROFILE_GENERATION=true` is set.
Missing stylometric profiles are filled with deterministic base values unless
`SSA_GENERATE_MISSING_STYLOMETRY=true` is explicitly set.

The Dockerized subjectivity-classifier service has its own isolated dependency
file at `services/subjectivity_classifier/requirements.txt`. Those legacy
TensorFlow dependencies are installed inside the Docker image, not inside the
main `env/` virtual environment.

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
../env/bin/python -m pip install -r requirements.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Frontend:

```bash
cd frontend
npm start
```

The frontend expects `REACT_APP_API_URL` to point at the backend.

## VS Code

Use `Run Full Project` from the Run and Debug panel. It runs `./start.sh`,
clears old local dev processes, starts Docker Compose for the subjectivity
sidecar, then starts the backend and frontend in a normal terminal process
without attaching the Python debugger.

## Runtime Shape

- `backend/main.py` exposes the chat API.
- `backend/app/api/chat.py` serves persona profiles and streams chat responses.
- `backend/app/` contains the API, biography generation, profile caching, provider configuration, data files, rate limits, and the guardrailed pipeline.
- `frontend/src/` contains the lightweight chat-only React interface.

## Documentation

- [Documentation Index](docs/README.md) lists all project documentation.
- [Model Provider Configuration](docs/model-provider-configuration.md) explains how to use one API key, one endpoint, and a chosen model.
- [SSA Guardrail Flow](docs/ssa-guardrail-flow.md) shows the simplified flow from user message to final validated response.
- [Guardrail Framework](docs/guardrail-framework.md) explains the layered guardrail pipeline in detail.
- [Red-Teaming Service](docs/red-teaming-service.md) explains automated red-teaming, LLM grading, and human mediation.
- [Subjectivity Classifier Sidecar](docs/subjectivity-classifier-sidecar.md) explains the Dockerized subjectivity classifier.
