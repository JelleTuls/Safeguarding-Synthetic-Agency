# Safeguarding Synthetic Social Agents

### Applied companion codebase for:

Safeguarding Synthetic Agency: A Framework for Measuring and Operationalizing System Integrity in Synthetic Social Agent Systems

This repository is the practical counterpart, or right hand, of the research
project with the same focus: safeguarding synthetic social agents. The thesis
develops the conceptual framework for SSA system integrity, while this codebase
operationalizes that framework as a runnable local system. It lets readers move
from the paper's claims to inspectable behavior: persona chat, lightweight versus
guardrailed generation, red-teaming evaluation, human score review, saved result
datasets, and reproducible computational-analysis plots.

The app serves 30 synthetic social agent profiles and exposes three connected
workspaces:

- **Chat:** open a persona chat and choose either the full guardrailed pipeline
  or the lightweight profile-only baseline before sending messages.
- **Red-teaming:** run single-turn adversarial prompt suites across manually
  selected profiles, compare lightweight and guardrailed answers, review scores,
  and save final JSON/PDF reports.
- **Computational analysis:** select saved red-team final-results JSON files and
  regenerate thesis-ready plots, tables, summaries, PNG exports, and report
  bundles.

## Public Research Artifact Notice

This repository is a thesis-facing research prototype. It is designed for local
inspection, demonstration, red-teaming experiments, and reproducible
computational analysis of the included reference dataset. It is **not** a
production safety product, hosted compliance service, or audited security
control.

For public reuse and academic reference:

- [License](LICENSE): MIT license for the codebase.
- [Citation](CITATION.cff): preferred software citation metadata.
- [Security Policy](SECURITY.md): how to handle sensitive issues or leaked
  secrets.
- [Contributing](CONTRIBUTING.md): development and data-handling guidance.
- [Release Notes](RELEASE_NOTES.md): thesis-artifact release summary and known
  limitations.

## For Supervisors And Second Readers

For an academic review of the repository, start with:

- [Reviewer Guide](docs/reviewer-guide.md): suggested reading order and demo
  path through the app.
- [Thesis To Code Map](docs/thesis-code-map.md): maps PBAR, TBAR, EB, SFAM, SC,
  and PG to implementation modules, prompt families, and computational plots.
- [Reproducibility Checklist](docs/reproducibility-checklist.md): clean-machine
  setup and repeatable red-team/analysis steps.
- [GitHub Branch Rules And Repository Protections](docs/github-protections.md):
  recommended public-repo rulesets, required checks, and security settings.
- [Reference Dataset](docs/reference-dataset.md): curated saved run and analysis
  artifacts for inspection without creating a new long run.
- [Limitations And Third-Party Components](docs/limitations-and-citations.md):
  known limitations, external software, and citation/reporting notes.

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

## Prerequisites

Before starting the app on a fresh machine, install:

- **Python 3.11 or newer**. Python 3.12 is recommended.
- **Node.js and npm**. Node 18+ or the current LTS release is recommended.
- **Docker Desktop** for full guardrail fidelity. The app can start without it,
  but Layer 08 then uses the deterministic subjectivity/objectivity fallback.
- **A Bash-compatible terminal**. On Windows, use WSL or Git Bash rather than
  PowerShell for the one-command launcher.
- **One LLM API key** for real chat and red-teaming runs. Without a key, the
  frontend and backend can still start, but model-backed chat/evaluator calls
  will fail with a configuration message.

Install Docker Desktop for your operating system:

- **macOS:** https://docs.docker.com/desktop/setup/install/mac-install/
- **Windows:** https://docs.docker.com/desktop/setup/install/windows-install/
- **Linux:** https://docs.docker.com/desktop/setup/install/linux/

After installing Docker, open Docker Desktop and wait until it says Docker is
running. You can check Docker Compose with:

```bash
docker compose version
```

If that command fails, the project still starts, but it runs Layer 08 in fallback
mode rather than with the Dockerized `fractalego/subjectivity_classifier`
sidecar.

## Quick Start

From the repository root, copy the environment examples:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

The examples already contain the local ports, default model names, frontend URL,
red-team service URL, subjectivity sidecar URL, verbose narrative logging, and
safe development toggles.
For normal local use, the only file most reviewers need to edit is
`backend/.env`.

Open `backend/.env` and fill **one** provider block:

- **Groq quick demo:** fill only `GROQ_API_KEY`; the Groq model and endpoint are
  already filled.
- **OpenAI:** fill only `OPENAI_API_KEY`; the default OpenAI endpoint and model
  are already filled.
- **Generic OpenAI-compatible gateway:** fill `LLM_API_KEY` and `LLM_BASE_URL`;
  change `LLM_MODEL` only if your provider uses a different model name.
- **Azure OpenAI:** fill `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_BASE_URL`, and
  `AZURE_OPENAI_MODEL` because Azure deployment names are project-specific.

Keep `LLM_PROVIDER=auto` unless you intentionally want to force one provider.
Do not commit `backend/.env` or `frontend/.env`; they are local configuration
files.

Then start the full local stack:

```bash
./start.sh
```

If your shell says the script is not executable, run:

```bash
chmod +x start.sh
./start.sh
```

On the first run, the launcher will:

- create `backend/.env` and `frontend/.env` from the examples if they are missing;
- create the Python virtual environment in `env/`;
- install backend and red-teaming Python packages;
- install frontend dependencies;
- start the Docker subjectivity-classifier sidecar when Docker Compose is available;
- fall back to the deterministic subjectivity scorer when Docker is unavailable;
- start the backend and frontend.

Open the app at:

```text
http://127.0.0.1:3000
```

The Red-teaming tab starts the standalone red-team service through the main
backend launcher endpoint, so a normal reviewer does not need a separate
terminal command for port `8010`. The Computational analysis tab reads finalized
JSON reports from `red_teaming/data/reports/` and writes generated artifacts to
`red_teaming/data/analysis/`.

## Port Map

| Service | Default URL | Started By |
| --- | --- | --- |
| React frontend | `http://127.0.0.1:3000` | `./start.sh` |
| Main backend API | `http://127.0.0.1:8000` | `./start.sh` |
| Subjectivity sidecar | `http://127.0.0.1:8001` | Docker Compose via `./start.sh` |
| Red-teaming service | `http://127.0.0.1:8010` | Red-teaming tab/backend launcher |

If you change `BACKEND_PORT` or `PORT` when launching, update
`frontend/.env` and `backend/.env` so the URLs still match.

## Environment Files

`backend/.env.example` and `frontend/.env.example` are intentionally
copy-ready. The values that can be safely prefilled are already filled in. After
copying, users normally only need to update:

- API keys or other secrets;
- a custom provider endpoint such as `LLM_BASE_URL` or `AZURE_OPENAI_BASE_URL`;
- a model/deployment name only when their provider requires a different one.

Provider priority with `LLM_PROVIDER=auto` is:

1. `LLM_API_KEY` + `LLM_MODEL` + `LLM_BASE_URL`
2. `AZURE_OPENAI_API_KEY` + `AZURE_OPENAI_MODEL` + `AZURE_OPENAI_BASE_URL`
3. `OPENAI_API_KEY` + `OPENAI_MODEL` + `OPENAI_BASE_URL`
4. `GROQ_API_KEY` or `GROQ_API_KEY_2` + `GROQ_MODEL` + `GROQ_BASE_URL`

For detailed provider examples, see
[Model Provider Configuration](docs/model-provider-configuration.md).

## Troubleshooting

- **`backend/.env does not appear to contain an LLM API key`:** the app can
  start, but chat and red-teaming need a configured provider key.
- **Docker is not running:** open Docker Desktop and wait until it is ready, then
  restart `./start.sh`. Without Docker, the app uses the fallback scorer.
- **Port already in use:** stop the old process or set another port, for example
  `PORT=3001 ./start.sh`. Keep `frontend/.env` aligned with any changed backend
  port.
- **`Permission denied: ./start.sh`:** run `chmod +x start.sh`.
- **Red-teaming page cannot connect to port `8010`:** open the Red-teaming tab
  once so the backend can launch the service, or start it manually with the
  command in the Manual Run section.

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

## Saved Results and Computational Analysis

Red-team runs are first stored as working run files in:

```text
red_teaming/data/runs/
```

When a run is finalized, the stable thesis/report files are written to:

```text
red_teaming/data/reports/
```

The frontend Analysis tab lists `*-final-results.json` files from that reports
folder. Selecting one report and clicking **Generate analysis** uses the same
backend analysis route as the red-team completion view. Regenerating analysis
for the same run overwrites the analysis folder for that run, which keeps plots
and summaries aligned with the currently saved dataset.

Generated computational-analysis artifacts are written to:

```text
red_teaming/data/analysis/<run_id>/
```

The analysis module creates normalized case tables, paired guardrailed-minus-
lightweight deltas, method/profile summaries, selected thesis figures, PNG plot
downloads at configurable pixel sizes, PDF/Markdown summaries, and a manifest
with warnings for skipped plots when optional fields such as `round_id`,
`style_distance`, or `adversarial_intensity` are absent.

## Curated Final Dataset And Plots

The repository intentionally keeps one final red-team dataset and its generated
analysis artifacts in git:

```text
rt-20260618-180138-af1204a6
```

This is the dataset used as the final reference run for the thesis-facing
computational analysis. Other working runs and old analysis folders are treated
as local runtime output and are not part of the cleaned handoff state.

Core result files:

- [Final results JSON](red_teaming/data/reports/rt-20260618-180138-af1204a6-final-results.json)
- [Final results PDF](red_teaming/data/reports/rt-20260618-180138-af1204a6-final-results.pdf)
- [Analysis manifest](red_teaming/data/analysis/rt-20260618-180138-af1204a6/manifest.json)
- [Analysis summary Markdown](red_teaming/data/analysis/rt-20260618-180138-af1204a6/summaries/analysis_summary.md)
- [Analysis summary PDF](red_teaming/data/analysis/rt-20260618-180138-af1204a6/summaries/analysis_summary.pdf)

Main thesis plots for this dataset:

- [Guardrail Effect Forest Plot](red_teaming/data/analysis/rt-20260618-180138-af1204a6/figures/paired_delta_forest.svg)
- [Pairwise Win Rate](red_teaming/data/analysis/rt-20260618-180138-af1204a6/figures/pairwise_win_rate.svg)
- [Guardrail Delta Heatmap](red_teaming/data/analysis/rt-20260618-180138-af1204a6/figures/guardrail_delta_heatmap.svg)
- [Failure Transition Matrix](red_teaming/data/analysis/rt-20260618-180138-af1204a6/figures/failure_transition_matrix.svg)
- [Score Distributions Boxplot](red_teaming/data/analysis/rt-20260618-180138-af1204a6/figures/score_distributions_boxplot.svg)
- [Delta ECDF By Method](red_teaming/data/analysis/rt-20260618-180138-af1204a6/figures/delta_ecdf_by_method.svg)
- [Performance-Stability Frontier](red_teaming/data/analysis/rt-20260618-180138-af1204a6/figures/stability_frontier.svg)

## Manual Run

The one-command `./start.sh` path is preferred. If you need to start services
manually for debugging, use four terminals from the repository root.

Install dependencies once:

```bash
python3 -m venv env
env/bin/python -m pip install --upgrade pip
env/bin/python -m pip install -r backend/requirements.txt -r red_teaming/requirements.txt
cd frontend
npm install
cd ..
```

Optional full-fidelity subjectivity sidecar:

```bash
docker compose up -d subjectivity-classifier
```

Backend API:

```bash
cd backend
SUBJECTIVITY_CLASSIFIER_URL=http://127.0.0.1:8001 \
  ../env/bin/python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Frontend:

```bash
cd frontend
npm start
```

Optional standalone red-teaming service for debugging:

```bash
cd red_teaming
../env/bin/python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8010
```

For normal use, the frontend calls the main backend endpoint
`POST /api/red-team/service/start`, and the backend starts the red-teaming
service automatically. The frontend expects `REACT_APP_API_URL` to point at the
backend and `REACT_APP_RED_TEAM_API_URL` to point at the red-teaming service.

## VS Code

The repository keeps two workspace tasks:

- **Prepare Full Project:** runs `bash scripts/prepare_project.sh` to create
  missing env files, install Python/frontend dependencies, and pre-build the
  optional subjectivity sidecar image when Docker Compose is available.
- **Start Full Project:** runs `./start.sh` to prepare anything still missing,
  start the optional Docker sidecar, and launch the backend plus frontend.

The Run and Debug panel also exposes **Run Full Project**, which calls
`./start.sh` in a normal terminal process without attaching the Python debugger.

## Runtime Shape

- `backend/main.py` exposes the chat API.
- `backend/app/api/chat.py` serves persona profiles and streams chat responses.
- `backend/app/` contains the API, biography generation, profile caching,
  provider configuration, data files, rate limits, the guardrailed pipeline, the
  dynamic request-intent signal, and the lightweight direct-response pipeline.
- `backend/app/lightweight/` contains the profile-only baseline that uses the
  copied base system prompt without the guardrail judge or post-processing.
- `red_teaming/` contains the standalone black-box evaluation service, prompt
  suite, evaluator LLM, optional human score overrides, JSON/PDF report
  generation, and computational-analysis package.
- `red_teaming/computational_analysis/` turns finalized red-team reports into
  reproducible thesis plots, CSV tables, PDF/Markdown summaries, and ZIP
  bundles.
- `frontend/src/` contains the React persona browser, chat interface, pipeline
  selector, red-team setup/review views, and computational-analysis workspace.

## Script Documentation

All first-party Python, JavaScript, and shell scripts include a top-of-file
description explaining their role in the system. The most important entry points
are:

- `start.sh`: prepares dependencies and starts the full local development stack.
- `scripts/prepare_project.sh`: prepares env files, dependencies, and the optional sidecar image without starting long-running servers.
- `scripts/smoke_check.sh`: compiles backend/red-team Python and builds the frontend.
- `backend/main.py`: ASGI entry point for the main FastAPI backend.
- `backend/app/server.py`: backend application factory and lifecycle wiring.
- `backend/app/services/chat_flow.py`: selects guardrailed or lightweight response generation.
- `backend/app/guardrails/dynamic_request.py`: interpretable request-intent signal used by judge, generator, and post-processors.
- `red_teaming/app/main.py`: standalone red-team FastAPI service.
- `red_teaming/app/runner.py`: black-box prompt executor for selected profiles and target modes.
- `red_teaming/app/llm_grader.py`: evaluator-LLM prompts for individual and pairwise scoring.
- `red_teaming/app/test_suites.py`: attaches method-level evaluation standards to editable prompts.
- `red_teaming/computational_analysis/pipeline.py`: reproducible tables, figures, summaries, and downloads from final reports.
- `red_teaming/prompt_script.py`: editable red-team prompt and expectation script.
- `frontend/src/App.js`: top-level React shell for Chat, Red-teaming, and Computational analysis tabs.

## Documentation

- [Documentation Index](docs/README.md) lists all project documentation.
- [Reviewer Guide](docs/reviewer-guide.md) gives a supervisor/second-reader
  review path through setup, demo, saved reports, and analysis.
- [Thesis To Code Map](docs/thesis-code-map.md) connects thesis concepts to code
  modules, red-team prompt families, and plots.
- [Reproducibility Checklist](docs/reproducibility-checklist.md) provides a
  clean-machine setup and regeneration checklist.
- [Reference Dataset](docs/reference-dataset.md) documents the curated saved run
  and its headline computational results.
- [Limitations And Third-Party Components](docs/limitations-and-citations.md)
  records prototype limits, external packages, and reporting notes.
- [Model Provider Configuration](docs/model-provider-configuration.md) explains how to use one API key, one endpoint, and a chosen model.
- [SSA Guardrail Flow](docs/ssa-guardrail-flow.md) shows the simplified flow from user message to final validated response.
- [Guardrail Framework](docs/guardrail-framework.md) explains the layered guardrail pipeline in detail.
- [Red-Teaming Service](docs/red-teaming-service.md) explains automated red-teaming, LLM grading, optional human overrides, and saved reports.
- [Computational Analysis](red_teaming/computational_analysis/README.md) explains the reproducible analysis package and thesis plot outputs.
- [Subjectivity Classifier Sidecar](docs/subjectivity-classifier-sidecar.md) explains the Dockerized subjectivity classifier.
