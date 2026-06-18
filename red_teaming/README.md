# Red Teaming Service

This service lives outside the main backend. It calls the existing chat API as a
black-box system under test, runs predefined guardrail test prompts against
selected SSA profiles, grades the answers with an evaluation LLM, and exposes API
endpoints plus review data for the integrated frontend.

The flow follows the red-teaming structure used in end-to-end LLM safety work:
attack selection, target execution, attack-success evaluation, safety scoring,
optional human adjudication, and final reporting. The current
implementation uses a manually authored static prompt corpus and single-turn
black-box attacks. The run metadata explicitly records the attack family,
interaction mode, target guardrail, and evaluation mode for every case, so
multi-turn or iterative adaptive attacks can be added later without changing the
main backend.

## Run

The easiest path is to run the project from the repository root:

```bash
./start.sh
```

Start the normal backend first if you are running services manually. In local
development, the main frontend can start this service for you through:

```text
POST http://127.0.0.1:8000/api/red-team/service/start
```

You can also start it manually for debugging:

```bash
cd red_teaming
../env/bin/python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8010
```

Open:

```text
http://127.0.0.1:8010
```

## Flow

1. Fetch available personas from the backend.
2. Use the manually selected profile ids, or sample a requested number of profiles when ids are not provided.
3. Execute 10 prompts per selected evaluation method:
   - PBAR: prompt-based attack resistance
   - TBAR: token-based attack resistance
   - EB: epistemic boundary adherence
   - SFAM: subjective framing and authority modulation
   - SC: stylometric consistency
   - PG: persuasive governance
4. For a full-analysis run, execute every prompt against both target modes:
   - `lightweight_no_guardrails`: direct persona response using the lightweight system prompt.
   - `guardrailed`: full layered guardrail pipeline.
5. Parse streamed backend events, including per-message analysis metadata.
6. Ask a grading LLM to judge the prompt, profile, response, target layer,
   expected behavior, expected style, expected metrics, and guardrail signals
   when available.
7. For full-analysis runs, ask the evaluator LLM to compare the lightweight and
   guardrailed answers to the same prompt. The pairwise score is blended with the
   individual LLM score; EB cases also apply deterministic ceilings for obvious
   epistemic-range overreach such as equations, advanced terminology, or
   practical expert advice outside the profile.
8. Human-in-the-loop scoring is optional. If the reviewer does not change a
   score, the original automated score is used. If the reviewer changes a score,
   that override is used in the final aggregates.
9. Produce profile-level, method-level, target-mode, and overall quantitative
   scores, including guardrailed-vs-lightweight deltas.
10. Save stable final JSON and PDF reports.

## Editing prompts and expected answers

The red-team prompt script is intentionally kept in one easy-to-edit file:

```text
red_teaming/prompt_script.py
```

Each prompt row contains:

- `message`: the exact user message fired at the SSA.
- `expected_answer`: the expected answer behavior for that prompt.

Because every run selects a random profile, `expected_answer` should stay
profile-neutral. It should describe the expected style, direction, response
type, boundary, and intensity, rather than naming a specific persona detail.
For example, an epistemic-boundary prompt should say that the SSA should answer
briefly, uncertainly, and without expert authority, not that it should mention a
specific job, city, or voting preference.

Runs can target the normal guardrailed backend path, the lightweight baseline
path, or the full analysis stack. The full analysis stack runs both pipelines for
the same selected profiles and prompts, which makes the final report useful for
comparing guarded and unguarded behavior.

## Main Scripts

- `app/main.py`: FastAPI routes for run creation, polling, review submission,
  prompt settings, report files, and static debug UI.
- `app/runner.py`: black-box executor that calls the backend chat endpoint,
  tracks progress, and applies individual and pairwise grading.
- `app/llm_grader.py`: evaluation-LLM prompts for individual case grading and
  guardrailed-vs-lightweight comparison.
- `app/scoring.py`: final score aggregation plus EB epistemic-range caps.
- `app/storage.py`: JSON persistence and final PDF/JSON report writing.
- `app/test_suites.py`: prompt-suite adapter that attaches metadata to
  `prompt_script.py`.
- `prompt_script.py`: editable user prompts and expected answer paragraphs.

## Frontend integration

The main React frontend can start a red-team run through the service. Set the
service URL with:

```text
REACT_APP_RED_TEAM_API_URL=http://127.0.0.1:8010
```

Before kickoff, the frontend lets the reviewer choose profiles manually, select
guardrail methods, edit expected-answer text, and choose guardrailed,
lightweight, or full-analysis-stack execution. During execution the frontend
shows the current profile, prompt, target mode, and x/y progress. After the run
completes, the integrated review panel shows one foldout per prompt with the
question, expected answer, expected style, expected SSA metrics, lightweight
answer, guardrailed answer, LLM reasoning, pairwise comparison reasoning, and
optional score controls. Final reports can be downloaded as JSON or PDF.

Run files are stored in `red_teaming/data/runs/`. Final saved reports are stored
in `red_teaming/data/reports/`.
