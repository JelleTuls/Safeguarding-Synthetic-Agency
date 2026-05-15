# Red Teaming Service

This service lives outside the main backend. It calls the existing chat API as a
black-box system under test, runs predefined guardrail test prompts against one
randomly selected SSA profile, computes preliminary scores, and exposes both API
endpoints and a small review UI for human mediation.

The flow follows the red-teaming structure used in end-to-end LLM safety work:
attack selection, target execution, attack-success evaluation, safety scoring,
human adjudication for ambiguous cases, and final reporting. The current
implementation uses a manually authored static prompt corpus and single-turn
black-box attacks. The run metadata explicitly records the attack family,
interaction mode, target guardrail, and evaluation mode for every case, so
multi-turn or iterative adaptive attacks can be added later without changing the
main backend.

## Run

Start the normal backend first. In local development, the main frontend can now
start this service for you through:

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
2. Randomly select one profile.
3. Execute 10 prompts per evaluation method:
   - PBAR: prompt-based attack resistance
   - TBAR: token-based attack resistance
   - EB: epistemic boundary adherence
   - SFAM: subjective framing and authority modulation
   - SC: stylometric consistency
   - PG: persuasive governance
4. Parse streamed backend events, including per-message analysis metadata.
5. Compute preliminary automated scores.
6. Flag ambiguous cases for human review.
7. Let the reviewer assign a numeric score and notes. Pass/fail is derived from
   the score (`score >= 0.5` means pass).
8. Produce final method-level and overall quantitative scores.
9. Save a stable final JSON report after human mediation is complete.

Runs can target either the normal guardrailed backend path or the lightweight
baseline path. The lightweight baseline keeps the persona prompt but asks the
backend to skip the guardrail judge, detectors, and post-processing. The same
red-team prompts and review workflow still run, which makes it useful for
comparing guarded and unguarded behavior.

## Frontend integration

The main React frontend can start a red-team run through the service. Set the
service URL with:

```text
REACT_APP_RED_TEAM_API_URL=http://127.0.0.1:8010
```

Before kickoff, the frontend lets the reviewer choose which guardrail methods
to test and whether to target the guardrailed or lightweight baseline path. When
a run starts, the page is blurred and a compact progress popup shows the current
method, prompt id, prompt text, completed cases, and current execution step. The
popup can request cancellation. After the run completes, the integrated review
panel shows method scores, grouped layer headers, prompts, model responses,
automated reasons, and pass/fail plus score controls for the human mediator.
Once pending human review reaches zero, the reviewer can save the final results
and download the JSON report.

Run files are stored in `red_teaming/data/runs/`. Final saved reports are stored
in `red_teaming/data/reports/`.
