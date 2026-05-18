# Frontend Interface

The frontend is a React interface for exploring the cached Synthetic Social
Agent profiles, chatting with an SSA, inspecting guardrail decisions, and
starting red-team evaluations.

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

The first screen loads the 30 cached persona profiles from the backend. Each
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

The app starts from cached base stylometric profiles. During a live chat, the
backend may stream updated stylometric or policy state, which the sidebar uses
for inspection.

## Red-Teaming Button And Flow

The main screen includes controls for starting a red-team evaluation. Before
starting, the user can select:

- which guardrail layers to test
- whether to test the guardrailed path or the lightweight no-guardrail baseline

When the red-team run starts, the page is blurred and a compact progress popup
shows the current method, prompt id, prompt text, and current process step. The
user can cancel the run from this popup.

After completion, the review panel shows a foldout list of prompts. Each row
shows the current score in a compact block. Opening a row reveals the prompt,
expected answer behavior, generated answer, rule score, LLM judge score, LLM
score reason, automated reasons, and human mediation controls.

Changing a human score between `0` and `1` updates the visible row score and the
method/overall score immediately. The review is auto-saved in the background.

Once all pending reviews are complete, the final result can be saved and
downloaded as a JSON report.
