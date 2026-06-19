# Frontend Interface

The frontend is a React interface for exploring the cached Synthetic Social
Agent profiles, chatting with an SSA, inspecting guardrail decisions, starting
red-team evaluations, and regenerating computational-analysis artifacts from
saved red-team datasets.

## Running The Frontend

The normal project launcher starts the frontend automatically:

```bash
./start.sh
```

Manual frontend run:

```bash
cd frontend
npm install
npm start
```

The frontend reads:

```env
REACT_APP_API_URL=http://127.0.0.1:8000
REACT_APP_RED_TEAM_API_URL=http://127.0.0.1:8010
```

## Main Screen

The app has three top-level tabs: Chat, Red-teaming, and Computational analysis.
The Chat screen loads the 30 cached persona profiles from the backend. Each
profile card represents one synthetic social agent. Selecting a profile opens a
chat popup for that agent.

The profile card and chat sidebar expose profile traits such as municipality,
gender, age group, education, and voting profile marker. These are not generated
at click time; they come from the cached profile set.

## Chat Popup

The chat popup has two main areas:

- **Profile sidebar:** biography, profile metadata, and stylometric state.
- **Conversation panel:** user messages, SSA responses, status bubbles, and the
  input field.

The close button in the top-right corner closes the popup. Pressing Enter or the
send-arrow button submits a message. Empty messages are ignored, and the input
is locked while a response is already being generated.

## Response Streaming And Typing

The backend streams events to the frontend. The frontend displays status bubbles
while the guardrail system is working and then renders the SSA answer as paced
chat bubbles. Persona responses use a typing effect so the user can see the
message appear gradually.

## Hover Inspection

Messages can include a small `i` inspection button. Hovering over or focusing
this button opens a floating analysis panel. The panel is positioned dynamically
so it stays inside the viewport.

For user messages, the hover panel can show pre-generation analysis such as:

- lexical prompt-injection signal
- topic relevance prompt
- epistemic boundary prompt
- authority and factuality framing signal

For SSA responses, the hover panel can show post-generation validation such as:

- final policy action
- selected topic category
- response mode
- authority and factuality level
- subjectivity/objectivity scores
- persuasive-governance scores
- rewrite or correction reasons

This hover inspection layer is useful for teaching and evaluation because it
shows why the visible response was accepted, softened, redirected, or rewritten.

## Stylometric State

The sidebar shows the current stylometric profile used as the persona's baseline
voice. This includes register, sentence style, vocabulary level, abstraction,
hedging, confidence, warmth, reasoning, and explanation style.

The app starts from cached base stylometric profiles. The sidebar keeps showing
that baseline profile so the user can compare the stable intended persona voice
against any adapted stylometric values shown inside response hover-inspection
panels.

## Red-Teaming Button And Flow

The main screen includes controls for starting a red-team evaluation. Before
starting, the user can select:

- which profiles to test
- which guardrail dimensions to test
- whether to run guardrailed, lightweight, or the full analysis stack

The full analysis stack runs both lightweight and guardrailed answers for the
same selected profiles and prompts, which enables paired comparison and
computational analysis.

When the red-team run starts, the page shows the current profile, target mode,
method, prompt id, prompt text, and x/y progress. The user can cancel the run
from the progress view.

After completion, the review panel shows a foldout list of prompts. Each row
shows the current lightweight and guardrailed score in compact form. Opening a
row reveals the prompt, expected answer behavior, expected style, expected SSA
metrics, lightweight answer, guardrailed answer, evaluator reasoning, pairwise
comparison reasoning, and optional human score controls.

Changing a human score between `0` and `1` updates the visible row score and the
method/overall score immediately. Human changes are optional; unchanged items
keep their automated evaluator score.

Final results can be saved and downloaded as JSON/PDF reports. The Red-teaming
tab also lists saved final reports so the user can reopen older runs without
rerunning the prompts.

## Computational Analysis Tab

The Computational analysis tab lists finalized `*-final-results.json` datasets.
After the user selects one dataset, the frontend can regenerate the analysis
through the backend proxy route. The result view shows headline averages, thesis
figures, plot captions, manifest warnings, per-plot PNG download controls, the
full dataset JSON download, and dataset removal for the JSON plus paired PDF.

Generated artifacts are stored under `red_teaming/data/analysis/<run_id>/`.
Regenerating analysis for a saved dataset overwrites that run's existing
analysis artifacts, keeping plots aligned with the current JSON report.
