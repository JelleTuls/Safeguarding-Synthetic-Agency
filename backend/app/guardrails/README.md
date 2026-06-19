# Guardrailed Flow

This document explains how a user message moves through the guardrail system before a final persona response is shown. The pipeline first gathers signals about broad request intent, lexical risk, topic relevance, epistemic fit, subjective framing, and writing style. A judge LLM then combines those signals into one policy decision. The response generator writes a draft under that policy, and the post-generation layers check whether the draft stayed within the expected subjectivity, authority, and persuasion limits.

The goal is not to silence the synthetic social agent, but to keep it responsible, profile-grounded, and bounded. The SSA can still express views, preferences, memories, and recommendations, but the system controls how factual, authoritative, persuasive, or emotionally forceful the final answer may become.

## Source Layout

Each guardrail module has a top-level description in its Python source file. The
folder numbers match the thesis-facing pipeline order:

- `01_lexical/`: hardcoded prompt-injection marker scan.
- `02_relevance/`: topic-profile relevance guidance for the judge LLM.
- `03_epistemic/`: epistemic range guidance for profile-level knowledge limits.
- `04_authority/`: pre-generation factuality and authority modulation signals.
- `05_stylometry/`: baseline speaking-style profile generation and guidance.
- `06_judge/`: LLM policy decision over the collected guardrail signals.
- `07_generator/`: guarded draft response generation and chat-bubble splitting.
- `08_subjective_framing_authority/`: post-generation subjectivity and authority validation.
- `09_persuasive_governance/`: post-generation persuasive-language validation.

Shared files include `schemas.py` for typed signal containers, `pipeline.py` for
layer orchestration, `engine.py` for the public guardrailed response entry point,
`dynamic_request.py` for broad user-intent signals, and `session_trace.py` for
local turn-by-turn inspection logs.

## Overview Diagram

```text
+==================================================================================================+
| CHAT REQUEST ENTRY                                                                                |
| app/services/chat_flow.py                                                                         |
| Mechanism: orchestration only                                                                     |
| Inputs: user message, (current session) chat history, persona details,                            |
|         persona country, client id                                                                |
| Prepares: biography, stylometric profile, session trace                                           |
+==================================================================================================+
                                                |
                                                v
+==================================================================================================+
| GUARDRAIL ENGINE ENTRY                                                                            |
| app/guardrails/engine.py                                                                          |
| Mechanism: orchestration only                                                                     |
| Builds GuardrailInput and starts the turn transcript                                              |
+==================================================================================================+
                                                |
                                                v
+--------------------------------------------------------------------------------------------------+
| STEP 00 - REQUEST LOGGING                                                                         |
| app/guardrails/pipeline.py                                                                        |
| Mechanism: trace logging only                                                                     |
| Records message, history size, biography length, and stylometric summary                          |
+--------------------------------------------------------------------------------------------------+
                                                |
                                                v
+--------------------------------------------------------------------------------------------------+
| LAYER 00B - DYNAMIC REQUEST-INTENT SIGNAL                                                         |
| app/guardrails/dynamic_request.py                                                                 |
| Mechanism: interpretable pattern groups; no LLM call                                              |
| Output: persuasion intent, style conflict, attack subtype, high-stakes/depth flags                |
+--------------------------------------------------------------------------------------------------+
                                                |
                                                v
+--------------------------------------------------------------------------------------------------+
| LAYER 01 - LEXICAL PROMPT-INJECTION SCAN                                                          |
| app/guardrails/01_lexical/engine.py                                                               |
| Mechanism: hardcoded list scan from 01_lexical/constants.py; no LLM prompt                        |
| Output: N/A                                                                                       |
+--------------------------------------------------------------------------------------------------+
                                                |
                                                v
+--------------------------------------------------------------------------------------------------+
| LAYER 02 - JUDGE-BASED TOPIC RELEVANCE SCORING                                                    |
| app/guardrails/02_relevance/engine.py                                                             |
| Mechanism: judge LLM prompt only; local secondary scoring placeholder is currently inactive       |
| Output: N/A                                                                                       |
+--------------------------------------------------------------------------------------------------+
                                                |
                                                v
+--------------------------------------------------------------------------------------------------+
| LAYER 03 - EPISTEMIC BOUNDARY PREPARATION                                                         |
| app/guardrails/03_epistemic/engine.py                                                             |
| Mechanism: prompt text only; builds an epistemic sub-prompt for the judge LLM                     |
| Output: N/A                                                                                       |
+--------------------------------------------------------------------------------------------------+
                                                |
                                                v
+--------------------------------------------------------------------------------------------------+
| LAYER 04 - PRE-GENERATION SUBJECTIVE FRAMING AND AUTHORITY MODULATION                             |
| app/guardrails/04_authority/engine.py                                                             |
| Mechanism: weighted fuzzy intent confidence plus five-level factuality prompt for judge LLM       |
| Output: N/A                                                                                       |
+--------------------------------------------------------------------------------------------------+
                                                |
                                                v
+--------------------------------------------------------------------------------------------------+
| LAYER 05 - STYLOMETRIC DESIGN PREPARATION                                                         |
| app/guardrails/05_stylometry/engine.py                                                            |
| Mechanism: cached/LLM-generated style profile plus stylometry sub-prompt for judge LLM            |
| Output: N/A                                                                                       |
+--------------------------------------------------------------------------------------------------+
                                                |
                                                v
+--------------------------------------------------------------------------------------------------+
| SIGNAL BUNDLE - PRE-JUDGE LAYER OUTPUTS                                                           |
| app/guardrails/pipeline.py                                                                        |
| Mechanism: orchestration only; bundles signals and judge sub-prompts without new LLM call         |
| Output: Combined final prompt (dynamic, lexical, relevance, epistemic, authority, stylometric)    |
+--------------------------------------------------------------------------------------------------+
                                                |
                                                v
+--------------------------------------------------------------------------------------------------+
| JUDGE PROMPT ASSEMBLY                                                                             |
| app/guardrails/06_judge/prompts.py                                                                |
| Collects: biography, history, user message, dynamic signal, lexical signal, Layer 02-05 prompts   |
| Adds: expertise, length, style, authority, fixed topic taxonomy, and JSON schema                  |
| Output: one combined judge user message plus GUARDRAILED_JUDGE_SYS_PROMPT                         |
+--------------------------------------------------------------------------------------------------+
                                                |
                                                v
+==================================================================================================+
| LAYER 06 - LLM-AS-A-JUDGE POLICY DECISION                                                         |
| app/guardrails/06_judge/engine.py                                                                 |
| Mechanism: sends combined judge prompt to LLM; parses structured JSON policy                      |
| Output: PolicyDecision(action, scores, topic category, response mode, authority, style controls)  |
+==================================================================================================+
                                                |
                                                v
+==================================================================================================+
| LAYER 07 - GUARDED RESPONSE GENERATION                                                            |
| app/guardrails/07_generator/engine.py                                                             |
| Mechanism: hardcoded generation heuristics plus guarded generation prompt to answering LLM        |
| Uses policy, style notes, authority notes, opening variation, biography, history, bubble hints    |
| Output: validated response split into paced chat-bubble events                                    |
+==================================================================================================+
                                                |
                                                v
+--------------------------------------------------------------------------------------------------+
| LAYER 08 - POST-GENERATION SUBJECTIVE FRAMING AND AUTHORITY VALIDATION                            |
| app/guardrails/08_subjective_framing_authority/engine.py                                          |
| Mechanism: Docker subjectivity service, local package, or deterministic fallback scorer           |
| Uses classifier probabilities plus topic and five-level factuality envelopes for rewrite logic    |
+--------------------------------------------------------------------------------------------------+
                                                |
                                                v
+--------------------------------------------------------------------------------------------------+
| LAYER 09 - PERSUASIVE GOVERNANCE                                                                  |
| app/guardrails/09_persuasive_governance/engine.py                                                 |
| Mechanism: detector score on generated response; rewrite prompt if persuasion is too high         |
| Uses chreh/persuasive_language_detector when available; fallback is only a runtime backup         |
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

## Layer 08 Sidecar Logic

Layer 08 uses the `fractalego/subjectivity_classifier` package to score the generated answer after Layer 07 has drafted it.

The package depends on an old TensorFlow 1.x stack, so the project runs it in a small Docker sidecar instead of installing it inside the main backend environment. Start it from the repository root:

```bash
docker compose up --build subjectivity-classifier
```

The backend connects through:

```bash
SUBJECTIVITY_CLASSIFIER_URL=http://127.0.0.1:8001
```

The sidecar receives the generated response at `POST /classify`, splits it into sentences, and returns:

- objective sentence list
- subjective sentence list
- per-sentence subjectivity/objectivity probabilities
- average `subjectivity_score`
- average `objectivity_score`

For best classifier quality, place the full GloVe file here:

```text
services/subjectivity_classifier/model/glove.6B.50d.txt
```

If that file is missing, the sidecar still runs with compact development
embeddings and logs a warning. If the sidecar is unreachable, Layer 08 tries a
local `subjectivity.classify` package. If no classifier package is available,
Layer 08 uses the backend's deterministic subjectivity/objectivity fallback
scorer. That fallback returns the same output shape, but it should be treated as
a sharing/development fallback rather than the highest-fidelity classifier mode.

On FastAPI startup, the backend starts a background warmup for Layer 08 and Layer 09 detectors. Layer 08 sends a tiny warmup classification to the configured subjectivity sidecar when available. Layer 09 loads the Hugging Face persuasion detector into memory. This keeps the first real user request from paying the cold-load cost when the services are ready.

## Layer Details

### Chat Request Entry

`app/services/chat_flow.py` is the outer orchestration layer. It receives the frontend request, resolves the persona biography, loads or creates the cached stylometric profile, creates or reuses a session trace for the client/persona conversation, and passes the runtime context into `app.guardrails.engine.generate_response`.

Biographies and stylometric profiles are cached in memory after the first disk load for the process. Missing profiles are still generated and persisted, but repeated turns for the same persona reuse the already loaded cache instead of re-reading the JSON files on every message.

The special `//biography` command is handled before normal model generation. All other chat messages enter the full guardrail flow.

### Guardrail Engine Entry

`app/guardrails/engine.py` converts runtime values into a `GuardrailInput`. This object carries the persona biography, stylometric profile, user message, chat history, and session trace through all later steps.

The engine also opens the turn transcript with the persona biography, stylometric profile, current user message, and prior chat history. This makes every downstream layer decision auditable from the same logged context.

### Step 00: Request Logging

`log_guardrailed_request` in `app/guardrails/pipeline.py` records the incoming user message and basic context before any guardrail decision is made.

It writes the user message, number of history turns, biography length, and stylometric summary into the session trace. This orchestration step does not classify or block anything; it establishes the baseline evidence for the turn.

### Layer 00b: Dynamic Request-Intent Signal

`app/guardrails/dynamic_request.py` extracts broad user-intent signals before
the numbered pre-generation guardrail layers run. It is deterministic and
interpretable, but it is intentionally not a final policy decision.

The signal captures request features that are easy to miss if the system only
looks at the final response: targeted or coercive persuasion intent, political
vote-influence framing, requested expert depth, high-stakes domains, style
requests that conflict with the persona's baseline voice, and recognizable
attack subtypes such as hidden prompt extraction or fake authority claims.

Later layers use this signal as additional evidence. The judge prompt receives
it as context, the generator can turn it into execution notes or static guarded
responses for clear attack subtypes, and Layer 09 can tighten persuasion
thresholds when the user asked for vote steering or targeted influence.

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

`app/guardrails/04_authority/engine.py` estimates whether the user is asking for factual explanation, uncertain interpretation, personal experience, belief, or preference. It does not make the final permission decision about how factual the answer may be; it only estimates the factuality level the user appears to request.

The layer uses a weighted confidence model rather than a small set of exact phrase matches. Individual words contribute evidence, fuzzy variants can still count, and nearby structure can raise confidence. For example, a word like `true` adds factual evidence on its own, while a verification frame such as a nearby form of `is` plus `it/this/that` raises confidence further. This makes the layer more tolerant of wording variation than a one-to-one string match.

Layer 04 now uses a five-level factuality scale:

- `belief_affirmation`: belief- or value-oriented framing with almost no factual authority
- `anecdotal`: personal lived-experience framing with only light factual support
- `subjective`: balanced persona-grounded interpretation with modest factual content
- `uncertain_interpretation`: cautious interpretation of factual material with clear uncertainty
- `limited_factual`: concise factual framing, only within the persona's realistic knowledge

When factual or verification-oriented confidence strongly dominates, the layer may request `limited_factual`. Weaker factual confidence becomes `uncertain_interpretation`. Strongly subjective confidence becomes `belief_affirmation` or `anecdotal`. Otherwise, the layer defaults to `subjective`.

The resulting `AuthoritySignal` includes `response_mode`, `factuality_level`, factual and subjective intent scores, `authority_level`, a summary, and a judge prompt. Layer 06 can lower this requested factuality level when relevance, epistemic score, knowledge level, detail permission, or expertise basis is weak. This means a user may ask for facts, but the final policy can still require a more subjective, anecdotal, or uncertain answer if the persona is not positioned to speak factually on that topic.

### Layer 05: Stylometric Design Preparation

`app/guardrails/05_stylometry/engine.py` turns the cached stylometric profile into judge guidance.

The profile can include register, sentence style, abstraction level, vocabulary level, hedging, confidence, warmth, explanation style, reasoning style, evidence, and a profile summary. These traits shape how the persona sounds, but they do not expand the persona's knowledge or override safety, relevance, or epistemic limits.

The rendered stylometry judge prompt is also cached per stable profile payload, so Layer 05 does not repeatedly rebuild identical prompt text for the same persona.

### Signal Bundle: Pre-Judge Layer Outputs

`build_guardrail_signals` in `app/guardrails/pipeline.py` combines all pre-judge outputs into one `GuardrailSignals` object.

The bundle contains the dynamic request, lexical, relevance, epistemic,
authority, and stylometric signals. This is the single structured input the
judge uses to make a policy decision.

### Judge Prompt Assembly

`build_judge_user_message` in `app/guardrails/06_judge/prompts.py` is where the LLM-facing pieces are collected into one judge request.

The assembled judge user message includes the persona biography, prior
conversation, current user message, user-message length signal, dynamic
request-intent signal, lexical detector output, the Layer 02 relevance judge
prompt, the Layer 03 epistemic judge prompt, the Layer 04 authority judge
prompt, and the Layer 05 stylometric judge prompt. It then appends shared judge
rules for expertise depth, response length, style modulation, authority, the
five factuality envelopes, the fixed topic-policy taxonomy from
`app/guardrails/topic_policy.py`, and the required JSON schema.

`app/guardrails/06_judge/engine.py` sends this combined user message together with `GUARDRAILED_JUDGE_SYS_PROMPT` to the judge LLM.

### Layer 06: LLM-As-A-Judge Policy Decision

`app/guardrails/06_judge/engine.py` builds the judge messages from the persona biography, chat history, current user message, and every upstream guardrail signal.

After parsing the judge's JSON, the engine applies broad dynamic-signal
constraints. These do not replace the judge; they make sure obvious request
intent is not lost in malformed or overly permissive judge output. Examples
include lowering the response action for targeted political persuasion,
preserving profile-level epistemic boundaries for high-depth out-of-range
requests, and keeping foreign style requests from overriding the baseline
stylometric profile.

The judge returns structured JSON. The parser normalizes the response into a `PolicyDecision` with these controls: `action`, rationale, response guidance, length target, detail permission, expertise basis, hedging and confidence style, register, sentence style, abstraction level, vocabulary level, explanation style, response mode, factuality level, authority level, `topic_policy_category`, `postprocessing_mode`, lexical score, relevance score, epistemic score, knowledge level, language level, tone, and emotional style.

The `topic_policy_category` is always normalized against the fixed taxonomy. If the judge omits it or returns an unsupported value, the parser falls back to `everyday_conversation`.

The `factuality_level` is also normalized to one of five levels: `belief_affirmation`, `anecdotal`, `subjective`, `uncertain_interpretation`, or `limited_factual`. Layer 08 later combines this factuality level with the topic category to compute the final subjectivity/objectivity expectation.

Supported actions are `allow`, `limited_answer`, `redirect`, and `refuse`. If the judge response is malformed or wrapped unexpectedly, the parser falls back to a cautious `limited_answer` policy.

The judge also chooses `postprocessing_mode`. `full` keeps the normal Layer 08 and Layer 09 classifier validation. `light` is allowed only for clearly safe tiny conversational turns such as greetings, thanks, simple social acknowledgement, or harmless everyday small talk. Even in light mode, the generator still follows the policy; the expensive post-generation classifiers are skipped only if the draft remains short, low-authority, allowed, and low-risk.

### Layer 07: Guarded Response Generation

`app/guardrails/07_generator/engine.py` turns the policy into executable generation guidance.

If the policy action is `refuse` or `redirect`, the generator returns a static
guarded response. Clear dynamic attack subtypes can also receive subtype-specific
static boundaries, such as refusing hidden prompt extraction or declining
targeted political persuasion. Otherwise, the generator resolves the final
length target, tightens guidance for low-fit or non-expert topics, adds
stylometric execution notes, authority execution notes, dynamic request notes,
and opening variation guidance, then calls the answering model with the persona
biography, guided user message, and chat history.

Opening variation is selected in `app/guardrails/opening_variation.py`. The system has 40 subjective opening strategies and 40 objective opening strategies. It does not provide canned first sentences; it selects a structural opening strategy such as beginning from a practical everyday preference, acknowledging complexity, separating facts from interpretation, or stating an evidence boundary. The generator is explicitly told to use the selected strategy as inspiration rather than copying the wording literally. The same variation system is also used by Layer 08 when a rewrite is needed, which helps prevent repeated rewrite openings such as `from my experience`.

The generator collects the draft response before streaming it. This is required because post-generation validation may correct the draft before the user sees the final answer. After validation, the final text is split into chat bubbles. The model may suggest bubble boundaries with `<BUBBLE_BREAK>`, and the backend also falls back to sentence-boundary splitting. Each outgoing bubble is preceded by a status event whose duration is calculated from the upcoming bubble's word count.

When `postprocessing_mode` is `light`, Layer 07 checks the finished draft before running expensive post-generation classifiers. If the policy is `allow`, the topic is low-risk, the authority is low, the factuality is subjective/anecdotal/belief-oriented, and the draft is under 35 words, Layer 08 and Layer 09 are skipped for that turn. If the judge clearly selects a very-short, everyday, low-authority answer but omits the new `postprocessing_mode` field, the parser falls back to `light`. The session trace records that the skip happened.

### Layer 08: Subjective Framing and Authority Validation

`app/guardrails/08_subjective_framing_authority/engine.py` is the first post-generation layer.

This layer checks whether the generated draft follows the response mode selected before generation. It uses the Layer 08 sidecar when `SUBJECTIVITY_CLASSIFIER_URL` is configured. The sidecar returns objective and subjective sentence lists plus soft probability scores.

The layer records the detector source, scoring mode, objective sentences, subjective sentences, `subjectivity_score`, and `objectivity_score`.

It then loads a combined expectation from `app/guardrails/topic_policy.py`. This combines the topic selected by Layer 06 with the five-level factuality level selected by Layer 06. The result tells Layer 08 how subjective, objective, and authoritative the generated answer is allowed to be.

When correction is needed, the layer asks the model to preserve meaning and persona voice while softening factual certainty and re-expressing claims as belief, experience, preference, or uncertainty. It also selects a fresh opening variation strategy for the rewritten answer.

### Layer 08 Calculation

Layer 08 uses four inputs:

- `topic_policy_category`: selected by Layer 06 from the 30-category fixed taxonomy in `app/guardrails/topic_policy.py`
- `factuality_level`: selected by Layer 06 from the five-level factuality scale
- `subjectivity_score` and `objectivity_score`: produced by `fractalego/subjectivity_classifier`
- `authority_level`: selected by Layer 06

The sidecar exposes classifier probabilities like this:

```json
{
  "subjectivity_score": 0.043346,
  "objectivity_score": 0.956654,
  "scoring": "softmax_probabilities",
  "sentences": [
    {
      "sentence": "I tend to support the VVD because it fits my practical outlook.",
      "label": "objective",
      "subjective_probability": 0.024387,
      "objective_probability": 0.975613
    }
  ]
}
```

For multiple sentences, Layer 08 averages the sentence-level probabilities:

```text
subjectivity_score = mean(sentence.subjective_probability)
objectivity_score  = mean(sentence.objective_probability)
```

If only the local package path is available, the package may return hard objective/subjective labels. In that fallback path, Layer 08 uses sentence-count ratios:

```text
subjectivity_score = subjective_sentence_count / total_sentence_count
objectivity_score  = objective_sentence_count / total_sentence_count
```

The final expectation is computed by combining:

- topic envelope: what is allowed for this topic
- factuality envelope: what is allowed for this requested response mode

The stricter bound wins:

```text
min_objectivity  = max(topic.min_objectivity, factuality.min_objectivity)
max_objectivity  = min(topic.max_objectivity, factuality.max_objectivity)
min_subjectivity = max(topic.min_subjectivity, factuality.min_subjectivity)
max_authority    = stricter(topic.max_authority, factuality.max_authority)
```

Example: Layer 06 selects `politics_government` and `subjective`.

```text
topic politics_government:
  max_objectivity  = 0.50
  min_subjectivity = 0.25
  max_authority    = low

factuality subjective:
  max_objectivity  = 0.60
  min_subjectivity = 0.30
  max_authority    = low

combined expectation:
  max_objectivity  = min(0.50, 0.60) = 0.50
  min_subjectivity = max(0.25, 0.30) = 0.30
  max_authority    = low
```

Layer 08 rewrites when any check fails:

```text
objectivity_score  < min_objectivity
objectivity_score  > max_objectivity
subjectivity_score < min_subjectivity
authority_level    > max_authority
```

Layer 08 uses a small `0.05` tolerance for classifier scores so harmless near-boundary cases, such as a short greeting classified as `0.618` objectivity against a `0.600` ceiling, do not trigger an unnecessary rewrite. Large misses still rewrite normally.

The log then shows one clear decision line:

```text
Layer 08 decision: topic=politics_government, factuality=subjective,
detector=subjectivity_classifier_service, scoring=softmax_probabilities,
classified_as=objective, subjectivity=0.036, objectivity=0.964,
will_rewrite=True, reasons=...
```

### Layer 09: Persuasive Governance

`app/guardrails/09_persuasive_governance/engine.py` is the second post-generation layer.

This layer checks whether the generated response moves beyond neutral explanation or soft recommendation into stronger persuasive pressure. It analyzes the generated answer, not the user message. Its intended detector is the Hugging Face model `chreh/persuasive_language_detector`.

The detector configuration lives in `app/guardrails/09_persuasive_governance/constants.py`:

```python
PERSUASION_MODEL_ID = "chreh/persuasive_language_detector"
PERSUASION_TOKENIZER_ID = "bert-large-cased"
PERSUASION_PIPELINE_TASK = "text-classification"
```

At runtime, Layer 09 loads the model through Hugging Face `transformers`:

```python
AutoTokenizer.from_pretrained("bert-large-cased")
AutoModelForSequenceClassification.from_pretrained("chreh/persuasive_language_detector")
pipeline(task="text-classification", ...)
```

The loader first tries `local_files_only=True`. This means that once the model is cached locally, normal requests can reuse the local files without contacting Hugging Face. If the local cache is missing, the loader tries the normal Hugging Face download path. If `transformers`, `torch`, or the model files are unavailable, Layer 09 falls back to the local marker-based detector and logs `heuristic_fallback`.

The package detector is applied sentence by sentence to the generated response. For each sentence, Layer 09 stores:

- the sentence text
- the raw Hugging Face classification output
- a normalized persuasion probability
- whether the sentence crosses the persuasive-sentence cutoff

The response-level persuasion score is the maximum sentence persuasion score. This keeps one strongly persuasive sentence from being hidden inside an otherwise neutral answer.

Layer 09 then reads the `topic_policy_category` selected by Layer 06 and loads that topic's `max_persuasion` threshold from `app/guardrails/topic_policy.py`. This means persuasion is not judged by one global cutoff. Everyday preference topics can allow more soft suggestion, while politics, religion, morality, finance, medical, legal, and other sensitive domains have stricter persuasion ceilings.

The effective threshold can be tightened further by the judge policy. For example, `limited_answer`, low relevance, or weak persona-domain fit can reduce the allowed persuasion ceiling. The trace logs the topic category, detector source, persuasion score, base topic threshold, effective threshold, threshold adjustments, persuasive sentences, sentence scores, and whether a rewrite happened.

A successful Hugging Face detector run appears in logs as:

```text
Layer 09 decision: topic=politics_government, detector=persuasive_language_detector,
persuasion=0.681, base_topic_threshold=0.250, effective_threshold=0.250,
adjustments=None, will_rewrite=True
```

If the external model cannot be used, the log will show:

```text
detector=heuristic_fallback
```

User-message persuasion handling is done earlier by the dynamic request signal
and the judge prompt in Layer 06. The system distinguishes a user asking what the
persona personally thinks from a user asking the persona to influence votes,
beliefs, family members, or another sensitive decision. Targeted or coercive
persuasion intent can lower the allowed action, tighten the persuasion
threshold, and add an autonomy boundary. If the user is only asking what the
persona itself thinks, prefers, believes, or voted for, the judge should allow a
bounded personal answer without adding an unnecessary autonomy boundary.

When Layer 09 correction is needed, the draft is withheld from the user and passed to the rewriting model. The rewrite prompt instructs the model to reduce directive, manipulative, emotionally pressuring, or belief-shaping language while preserving the useful conversational function of the answer. Recommendations must remain soft, contextual, balanced, and easy to decline.

### Final Response and Trace Closing

After Layer 09, the final accepted or corrected response is yielded to the frontend and appended to the session trace.

The trace includes request context, each guardrail signal, judge prompts and raw response, the normalized policy, generation guidance, post-generation detector sources, post-generation scores, correction reasons, draft response when changed, and the final response. The result is a readable per-session audit record under `app/guardrails/log/`.

## Layer Folders

Each numbered folder maps to one methodological layer. Hardcoded comparison lists live in that layer's `constants.py` file when used. Prompt text lives in that layer's `prompts.py` file when the layer contributes LLM instructions. The shared topic-policy taxonomy used by Layer 06 and Layer 08 lives in `app/guardrails/topic_policy.py`.

```text
+-------------------------------+-------------------------------------+----------------------------------------------+
| Folder                        | Main role                           | Important files                              |
+-------------------------------+-------------------------------------+----------------------------------------------+
| 01_lexical                    | Prompt-injection lexical scan       | engine.py, constants.py                      |
| 02_relevance                  | Judge-based topic relevance         | engine.py, prompts.py                        |
| 03_epistemic                  | Epistemic judge preparation         | engine.py, prompts.py                        |
| 04_authority                  | Pre-generation response mode        | engine.py, constants.py, prompts.py          |
| 05_stylometry                 | Stylometric profile and guidance    | engine.py, store.py, prompts.py              |
| shared                        | Policy, openings, request intent    | topic_policy.py, opening_variation.py, dynamic_request.py |
| 06_judge                      | LLM-as-a-judge policy decision      | engine.py, prompts.py                        |
| 07_generator                  | Guarded response generation         | engine.py, constants.py, prompts.py          |
| 08_subjective_framing_authority | Subjectivity/authority validation | engine.py, constants.py, prompts.py          |
| 09_persuasive_governance      | Persuasion validation               | engine.py, constants.py, prompts.py          |
+-------------------------------+-------------------------------------+----------------------------------------------+
```

## Data Objects

`GuardrailInput` carries the runtime context: persona biography, stylometric profile, user message, chat history, and session trace.

`GuardrailSignals` carries all pre-judge signals: dynamic request intent,
lexical, relevance, epistemic, authority, and stylometric. For relevance, this
means the judge-facing relevance prompt, not a locally computed topic-overlap
score.

`PolicyDecision` is the judge's normalized control object. It determines whether to allow, limit, redirect, or refuse, and it supplies the generator with the final judge-produced relevance score, response length, detail permission, epistemic limits, style constraints, response mode, factuality level, authority level, and topic policy category.
