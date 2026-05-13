# Guardrailed Flow

Every persona chat message uses the same full guardrailed path. There is no lightweight alternate path.

## Optional Classifier Sidecar

Layer 08 can use a Dockerized `fractalego/subjectivity_classifier` service because the original package depends on TensorFlow 1.x and cannot be installed cleanly in the modern backend Python environment.

Start the sidecar from the repository root:

```bash
docker compose up --build subjectivity-classifier
```

Then configure the backend:

```bash
SUBJECTIVITY_CLASSIFIER_URL=http://127.0.0.1:8001
```

When the variable is set, Layer 08 calls `POST /classify` on the sidecar first. If the sidecar is unavailable, Layer 08 falls back to a locally importable `subjectivity.classify` module, and then to local heuristic markers.

## Overview Diagram

```text
+==================================================================================================+
| CHAT REQUEST ENTRY                                                                                |
| app/services/chat_flow.py                                                                         |
| Mechanism: orchestration only; no hardcoded guardrail list and no LLM prompt                      |
| Inputs: user message, chat history, persona details, persona country, client id                   |
| Prepares: biography, stylometric profile, session trace                                           |
+==================================================================================================+
                                                |
                                                v
+==================================================================================================+
| GUARDRAIL ENGINE ENTRY                                                                            |
| app/guardrails/engine.py                                                                          |
| Mechanism: orchestration only; no hardcoded guardrail list and no LLM prompt                      |
| Builds GuardrailInput and starts the turn transcript                                              |
+==================================================================================================+
                                                |
                                                v
+--------------------------------------------------------------------------------------------------+
| STEP 00 - REQUEST LOGGING                                                                         |
| app/guardrails/pipeline.py                                                                        |
| Mechanism: trace logging only; no hardcoded guardrail list and no LLM prompt                      |
| Records message, history size, biography length, and stylometric summary                          |
+--------------------------------------------------------------------------------------------------+
                                                |
                                                v
+--------------------------------------------------------------------------------------------------+
| LAYER 01 - LEXICAL PROMPT-INJECTION SCAN                                                          |
| app/guardrails/01_lexical/engine.py                                                               |
| Mechanism: hardcoded list scan from 01_lexical/constants.py; no LLM prompt                        |
| Output: LexicalSignal(triggered, matched_terms, risk_level)                                       |
+--------------------------------------------------------------------------------------------------+
                                                |
                                                v
+--------------------------------------------------------------------------------------------------+
| LAYER 02 - JUDGE-BASED TOPIC RELEVANCE SCORING                                                    |
| app/guardrails/02_relevance/engine.py                                                             |
| Mechanism: judge LLM prompt only; local secondary scoring placeholder is currently inactive       |
| Output: RelevanceSignal(summary, judge prompt; local score fields are placeholders)               |
+--------------------------------------------------------------------------------------------------+
                                                |
                                                v
+--------------------------------------------------------------------------------------------------+
| LAYER 03 - EPISTEMIC BOUNDARY PREPARATION                                                         |
| app/guardrails/03_epistemic/engine.py                                                             |
| Mechanism: prompt text only; builds an epistemic sub-prompt for the judge LLM                     |
| Output: EpistemicSignal(summary, judge prompt)                                                    |
+--------------------------------------------------------------------------------------------------+
                                                |
                                                v
+--------------------------------------------------------------------------------------------------+
| LAYER 04 - PRE-GENERATION SUBJECTIVE FRAMING AND AUTHORITY MODULATION                             |
| app/guardrails/04_authority/engine.py                                                             |
| Mechanism: hardcoded intent markers plus five-level factuality sub-prompt for the judge LLM       |
| Output: AuthoritySignal(response_mode, factuality_level, intent scores, authority, judge prompt)  |
+--------------------------------------------------------------------------------------------------+
                                                |
                                                v
+--------------------------------------------------------------------------------------------------+
| LAYER 05 - STYLOMETRIC DESIGN PREPARATION                                                         |
| app/guardrails/05_stylometry/engine.py                                                            |
| Mechanism: cached/LLM-generated style profile plus stylometry sub-prompt for judge LLM            |
| Output: StylometricSignal(summary, judge prompt)                                                  |
+--------------------------------------------------------------------------------------------------+
                                                |
                                                v
+--------------------------------------------------------------------------------------------------+
| SIGNAL BUNDLE - PRE-JUDGE LAYER OUTPUTS                                                           |
| app/guardrails/pipeline.py                                                                        |
| Mechanism: orchestration only; bundles signals and judge sub-prompts without new LLM call         |
| Output: GuardrailSignals(lexical, relevance, epistemic, authority, stylometric)                   |
+--------------------------------------------------------------------------------------------------+
                                                |
                                                v
+--------------------------------------------------------------------------------------------------+
| JUDGE PROMPT ASSEMBLY                                                                             |
| app/guardrails/06_judge/prompts.py                                                                |
| Collects: biography, history, user message, lexical signal, and Layer 02-05 judge sub-prompts     |
| Adds: judge expertise, length, style, authority rules, and required JSON response schema          |
| Output: one combined judge user message plus GUARDRAILED_JUDGE_SYS_PROMPT                         |
+--------------------------------------------------------------------------------------------------+
                                                |
                                                v
+==================================================================================================+
| LAYER 06 - LLM-AS-A-JUDGE POLICY DECISION                                                         |
| app/guardrails/06_judge/engine.py                                                                 |
| Mechanism: sends combined judge prompt to LLM; parses structured JSON policy                      |
| Output: PolicyDecision(action, scores, detail limits, response mode, authority, style controls)   |
+==================================================================================================+
                                                |
                                                v
+==================================================================================================+
| LAYER 07 - GUARDED RESPONSE GENERATION                                                            |
| app/guardrails/07_generator/engine.py                                                             |
| Mechanism: hardcoded generation heuristics plus guarded generation prompt to answering LLM        |
| Uses policy guidance, biography, chat history, style notes, authority notes, and bubble hints     |
| Output: validated response split into paced chat-bubble events                                    |
+==================================================================================================+
                                                |
                                                v
+--------------------------------------------------------------------------------------------------+
| LAYER 08 - POST-GENERATION SUBJECTIVE FRAMING AND AUTHORITY VALIDATION                            |
| app/guardrails/08_subjective_framing_authority/engine.py                                          |
| Mechanism: Docker subjectivity service, local package, or fallback lists; rewrite if needed       |
| Uses fractalego/subjectivity_classifier when sidecar/local package is available                   |
+--------------------------------------------------------------------------------------------------+
                                                |
                                                v
+--------------------------------------------------------------------------------------------------+
| LAYER 09 - PERSUASIVE GOVERNANCE                                                                  |
| app/guardrails/09_persuasive_governance/engine.py                                                 |
| Mechanism: persuasive_language_detector or fallback lists; rewrite prompt if persuasion is high   |
| Uses chreh/persuasive_language_detector when available; may regenerate lower-pressure wording     |
+--------------------------------------------------------------------------------------------------+
                                                |
                                                v
+==================================================================================================+
| FINAL RESPONSE AND TRACE CLOSING                                                                  |
| app/api/chat.py, app/guardrails/session_trace.py                                                  |
| Mechanism: streaming and trace writing only; no hardcoded guardrail list and no LLM prompt        |
| Streams final accepted/corrected response and writes the full readable turn trace                 |
+==================================================================================================+
```

## Layer Details

### Chat Request Entry

`app/services/chat_flow.py` is the outer orchestration layer. It receives the frontend request, resolves the persona biography, loads or creates the cached stylometric profile, creates or reuses a session trace for the client/persona conversation, and passes the runtime context into `app.guardrails.engine.generate_response`.

The special `//biography` command is handled before normal model generation. All other chat messages enter the full guardrail flow.

### Guardrail Engine Entry

`app/guardrails/engine.py` converts runtime values into a `GuardrailInput`. This object carries the persona biography, stylometric profile, user message, chat history, and session trace through all later steps.

The engine also opens the turn transcript with the persona biography, stylometric profile, current user message, and prior chat history. This makes every downstream layer decision auditable from the same logged context.

### Step 00: Request Logging

`log_guardrailed_request` in `app/guardrails/pipeline.py` records the incoming user message and basic context before any guardrail decision is made.

It writes the user message, number of history turns, biography length, and stylometric summary into the session trace. This orchestration step does not classify or block anything; it establishes the baseline evidence for the turn.

### Layer 01: Lexical Prompt-Injection Scan

`app/guardrails/01_lexical/engine.py` performs a direct lexical scan against `PROMPT_INJECTION_TERMS`.

It produces a `LexicalSignal` with three fields: whether a term triggered, which terms matched, and a risk level of `high` or `low`. This is an early warning layer for obvious prompt-injection and system-extraction language. It is intentionally narrow and is later interpreted by the judge rather than treated as the whole safety decision.

### Layer 02: Judge-Based Topic Relevance Scoring

`app/guardrails/02_relevance/engine.py` prepares relevance instructions for the judge LLM and keeps a placeholder function for a future optional secondary relevance-scoring mechanism. That placeholder is inactive and returns no score.

Layer 02 returns a `RelevanceSignal` containing a summary and a judge sub-prompt. The existing numeric fields on `RelevanceSignal` are kept only as compatibility placeholders. The actual relevance score used by the system is produced later by Layer 06, where the judge LLM compares the user message against the persona biography and profile context.

### Layer 03: Epistemic Boundary Preparation

`app/guardrails/03_epistemic/engine.py` prepares an epistemic judge prompt rather than making the final epistemic decision itself.

The generated `EpistemicSignal` instructs the judge to assess what the persona could realistically know, how deeply the persona should reason, and whether the response should remain basic, cautious, or limited. The purpose is to prevent the SSA from becoming a generic expert assistant when the biography does not support that authority.

### Layer 04: Pre-Generation Subjective Framing and Authority Modulation

`app/guardrails/04_authority/engine.py` inspects the user message for factual-intent markers and subjective-intent markers. It does not make the final permission decision about how factual the answer may be; it estimates the factuality level the user appears to request.

Layer 04 now uses a five-level factuality scale:

- `belief_affirmation`: belief- or value-oriented framing with almost no factual authority
- `anecdotal`: personal lived-experience framing with only light factual support
- `subjective`: balanced persona-grounded interpretation with modest factual content
- `uncertain_interpretation`: cautious interpretation of factual material with clear uncertainty
- `limited_factual`: concise factual framing, only within the persona's realistic knowledge

When factual or verification-oriented markers strongly dominate, the layer may request `limited_factual`. Weaker factual requests become `uncertain_interpretation`. Strongly subjective prompts become `belief_affirmation` or `anecdotal`. Otherwise, the layer defaults to `subjective`.

The resulting `AuthoritySignal` includes `response_mode`, `factuality_level`, factual and subjective intent scores, `authority_level`, a summary, and a judge prompt. Layer 06 can lower this requested factuality level when relevance, epistemic score, knowledge level, detail permission, or expertise basis is weak. This means a user may ask for facts, but the final policy can still require a more subjective, anecdotal, or uncertain answer if the persona is not positioned to speak factually on that topic.

### Layer 05: Stylometric Design Preparation

`app/guardrails/05_stylometry/engine.py` turns the cached stylometric profile into judge guidance.

The profile can include register, sentence style, abstraction level, vocabulary level, hedging, confidence, warmth, explanation style, reasoning style, evidence, and a profile summary. These traits shape how the persona sounds, but they do not expand the persona's knowledge or override safety, relevance, or epistemic limits.

### Signal Bundle: Pre-Judge Layer Outputs

`build_guardrail_signals` in `app/guardrails/pipeline.py` combines all pre-judge outputs into one `GuardrailSignals` object.

The bundle contains the lexical, relevance, epistemic, authority, and stylometric signals. This is the single structured input the judge uses to make a policy decision.

### Judge Prompt Assembly

`build_judge_user_message` in `app/guardrails/06_judge/prompts.py` is where the LLM-facing pieces are collected into one judge request.

The assembled judge user message includes the persona biography, prior conversation, current user message, user-message length signal, lexical detector output, the Layer 02 relevance judge prompt, the Layer 03 epistemic judge prompt, the Layer 04 authority judge prompt, and the Layer 05 stylometric judge prompt. It then appends shared judge rules for expertise depth, response length, style modulation, authority, and the required JSON schema.

`app/guardrails/06_judge/engine.py` sends this combined user message together with `GUARDRAILED_JUDGE_SYS_PROMPT` to the judge LLM.

### Layer 06: LLM-As-A-Judge Policy Decision

`app/guardrails/06_judge/engine.py` builds the judge messages from the persona biography, chat history, current user message, and every upstream guardrail signal.

The judge returns structured JSON. The parser normalizes the response into a `PolicyDecision` with these controls: `action`, rationale, response guidance, length target, detail permission, expertise basis, hedging and confidence style, register, sentence style, abstraction level, vocabulary level, explanation style, response mode, authority level, lexical score, relevance score, epistemic score, knowledge level, language level, tone, and emotional style.

Supported actions are `allow`, `limited_answer`, `redirect`, and `refuse`. If the judge response is malformed or wrapped unexpectedly, the parser falls back to a cautious `limited_answer` policy.

### Layer 07: Guarded Response Generation

`app/guardrails/07_generator/engine.py` turns the policy into executable generation guidance.

If the policy action is `refuse` or `redirect`, the generator returns a static guarded response. Otherwise, it resolves the final length target, tightens guidance for low-fit or non-expert topics, adds stylometric and authority execution notes, and calls the answering model with the persona biography, guided user message, and chat history.

The generator collects the draft response before streaming it. This is required because post-generation validation may correct the draft before the user sees the final answer. After validation, the final text is split into chat bubbles. The model may suggest bubble boundaries with `<BUBBLE_BREAK>`, and the backend also falls back to sentence-boundary splitting. Each outgoing bubble is preceded by a status event whose duration is calculated from the upcoming bubble's word count.

### Layer 08: Subjective Framing and Authority Validation

`app/guardrails/08_subjective_framing_authority/engine.py` is the first post-generation layer.

This layer checks whether the generated draft follows the response mode selected before generation. It first calls the optional Docker sidecar when `SUBJECTIVITY_CLASSIFIER_URL` is configured. The sidecar runs `fractalego/subjectivity_classifier` in a legacy TensorFlow 1.x environment and returns objective and subjective sentence lists over HTTP.

If the sidecar is not configured, the layer tries `fractalego/subjectivity_classifier` through `python -m subjectivity.classify` when the package is installed locally. If neither classifier path is available, the layer falls back to local subjectivity and objectivity markers so the application can still run during development.

The layer computes subjectivity and objectivity scores, tracks the detector source, and records objective and subjective sentences. It triggers correction when a non-factual response mode becomes too factual or authoritative, or when limited-expertise disclaimers are repeated or unnecessary for low-stakes personal advice.

When correction is needed, the layer asks the model to preserve meaning and persona voice while softening factual certainty, re-expressing claims as belief, experience, preference, or uncertainty, and removing unnecessary expertise disclaimers.

### Layer 09: Persuasive Governance

`app/guardrails/09_persuasive_governance/engine.py` is the second post-generation layer.

This layer checks whether the response moves beyond neutral or soft recommendation into stronger persuasive pressure. It uses Hugging Face `transformers` with `chreh/persuasive_language_detector` when the model stack is available. If not, it falls back to local persuasive markers.

The layer computes a persuasion score, tracks persuasive sentences, and records whether the package detector or fallback detector was used. It treats high persuasive pressure as corrective, and also treats moderate persuasive pressure as corrective when the topic is sensitive, the relevance score is low, or the policy action is already constrained.

When correction is needed, the model is instructed to reduce directive, manipulative, emotionally pressuring, or belief-shaping language. Recommendations must remain soft, contextual, balanced, and easy to decline.

### Final Response and Trace Closing

After Layer 09, the final accepted or corrected response is yielded to the frontend and appended to the session trace.

The trace includes request context, each guardrail signal, judge prompts and raw response, the normalized policy, generation guidance, post-generation detector sources, post-generation scores, correction reasons, draft response when changed, and the final response. The result is a readable per-session audit record under `app/guardrails/log/`.

## Layer Folders

Each numbered folder maps to one methodological layer. Hardcoded comparison lists live in that layer's `constants.py` file when used. Prompt text lives in that layer's `prompts.py` file when the layer contributes LLM instructions.

```text
+-------------------------------+-------------------------------------+----------------------------------------------+
| Folder                        | Main role                           | Important files                              |
+-------------------------------+-------------------------------------+----------------------------------------------+
| 01_lexical                    | Prompt-injection lexical scan       | engine.py, constants.py                      |
| 02_relevance                  | Judge-based topic relevance         | engine.py, prompts.py                        |
| 03_epistemic                  | Epistemic judge preparation         | engine.py, prompts.py                        |
| 04_authority                  | Pre-generation response mode        | engine.py, constants.py, prompts.py          |
| 05_stylometry                 | Stylometric profile and guidance    | engine.py, store.py, prompts.py              |
| 06_judge                      | LLM-as-a-judge policy decision      | engine.py, prompts.py                        |
| 07_generator                  | Guarded response generation         | engine.py, constants.py, prompts.py          |
| 08_subjective_framing_authority | Subjectivity/authority validation | engine.py, constants.py, prompts.py          |
| 09_persuasive_governance      | Persuasion validation               | engine.py, constants.py, prompts.py          |
+-------------------------------+-------------------------------------+----------------------------------------------+
```

## Data Objects

`GuardrailInput` carries the runtime context: persona biography, stylometric profile, user message, chat history, and session trace.

`GuardrailSignals` carries all pre-judge signals: lexical, relevance, epistemic, authority, and stylometric. For relevance, this means the judge-facing relevance prompt, not a locally computed topic-overlap score.

`PolicyDecision` is the judge's normalized control object. It determines whether to allow, limit, redirect, or refuse, and it supplies the generator with the final judge-produced relevance score, response length, detail permission, epistemic limits, style constraints, response mode, factuality level, and authority level.
