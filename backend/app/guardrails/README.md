# Guardrailed Flow

Every persona chat message uses this flow.

```text
+--------------------------------------------------------------------------------------------------+
| CHAT REQUEST ENTRY                                                                               |
| File: app/services/chat_flow.py                                                                   |
| The frontend sends a user message, persona details, persona country, and chat history. The        |
| service resolves the persona biography, loads or creates the persona stylometric profile, creates |
| a session trace, and forwards all runtime context into the guardrailed response engine.           |
+--------------------------------------------------------------------------------------------------+
                                                |
                                                v
+--------------------------------------------------------------------------------------------------+
| STEP 0 - REQUEST LOGGING                                                                          |
| File: app/guardrails/pipeline.py                                                                  |
| The pipeline records the incoming user message, chat-history length, biography length, and        |
| stylometric profile summary. This creates an interpretable trace of the exact context used by     |
| the guardrail system before any safety or alignment decision is made.                             |
+--------------------------------------------------------------------------------------------------+
                                                |
                                                v
+--------------------------------------------------------------------------------------------------+
| STEP 1A - INITIAL LEXICAL GUARDRAIL                                                               |
| File: app/guardrails/01_lexical/engine.py                                                            |
| The user message is scanned for high-risk prompt-injection and system-extraction patterns such    |
| as requests to reveal hidden instructions, ignore previous instructions, expose API keys, or      |
| disable guardrails. The output is a LexicalSignal containing whether the scan triggered, which    |
| terms matched, and the risk level. This signal is not the whole defense; it is an early warning   |
| passed into later judgment.                                                                       |
+--------------------------------------------------------------------------------------------------+
                                                |
                                                v
+--------------------------------------------------------------------------------------------------+
| STEP 1B - SEMANTIC TOPIC-DISTANCE RELEVANCE SCORING                                               |
| File: app/guardrails/02_relevance/engine.py                                                          |
| The system compares the user message against salient terms from the persona biography and a small |
| set of domain-neighbor terms. It computes a semantic similarity score and semantic distance score |
| that estimate whether the request is close to the SSA's profile, interests, biography, and likely |
| conversational scope. These scores guide whether the response can be full, limited, redirected,   |
| or refused.                                                                                       |
+--------------------------------------------------------------------------------------------------+
                                                |
                                                v
+--------------------------------------------------------------------------------------------------+
| STEP 1C - EPISTEMIC BOUNDARY ENFORCEMENT PREPARATION                                              |
| File: app/guardrails/03_epistemic/engine.py                                                          |
| The pipeline prepares judge instructions for evaluating whether the persona should realistically  |
| know about the requested topic and how deeply it should reason. The judge is asked to infer       |
| knowledge level, language level, tone, emotional style, and permitted reasoning depth from the    |
| biography rather than letting the model act as a generic expert assistant.                        |
+--------------------------------------------------------------------------------------------------+
                                                |
                                                v
+--------------------------------------------------------------------------------------------------+
| STEP 1D - SUBJECTIVE FRAMING AND AUTHORITY MODULATION                                             |
| File: app/guardrails/04_authority/engine.py                                                          |
| The user message is evaluated for epistemic intent. Factual or verification-oriented prompts can |
| select limited_factual mode, while opinion, concern, preference, and social interpretation prompts|
| keep the default subjective/persona-grounded mode. The output controls how much authority the     |
| SSA may use and whether it should frame the answer as fact, belief, lived experience, preference, |
| or uncertainty.                                                                                   |
+--------------------------------------------------------------------------------------------------+
                                                |
                                                v
+--------------------------------------------------------------------------------------------------+
| STEP 1E - STYLOMETRIC DESIGN PREPARATION                                                          |
| File: app/guardrails/05_stylometry/engine.py                                                         |
| The persona's cached stylometric profile is transformed into judge guidance. Traits such as       |
| register, sentence style, abstraction level, vocabulary level, hedging, confidence, warmth, and   |
| explanation style define the SSA's baseline speaking signature. These traits shape expression     |
| without expanding the persona's knowledge or overriding safety decisions.                         |
+--------------------------------------------------------------------------------------------------+
                                                |
                                                v
+--------------------------------------------------------------------------------------------------+
| STEP 1F - GUARDRAIL SIGNAL BUNDLE                                                                 |
| File: app/guardrails/pipeline.py                                                                  |
| The lexical, relevance, epistemic, authority, and stylometric outputs are bundled into one        |
| GuardrailSignals object. This bundle gives the judge a consolidated view of safety risk, topic    |
| fit, epistemic fit, intended subjectivity/authority mode, and communication style.                |
+--------------------------------------------------------------------------------------------------+
                                                |
                                                v
+--------------------------------------------------------------------------------------------------+
| STEP 2 - LLM-AS-A-JUDGE POLICY DECISION                                                           |
| File: app/guardrails/06_judge/engine.py                                                              |
| A separate judging model receives the persona biography, chat history, user message, and all      |
| upstream guardrail signals. It returns structured JSON selecting an action: allow, limited_answer,|
| redirect, or refuse. It also returns relevance and epistemic scores, detail permission, expertise |
| basis, length target, response mode, authority level, and style-control fields for the generator. |
+--------------------------------------------------------------------------------------------------+
                                                |
                                                v
+--------------------------------------------------------------------------------------------------+
| STEP 3 - GUARDED RESPONSE GENERATION                                                              |
| File: app/guardrails/07_generator/engine.py                                                          |
| The answering model receives the original user message plus the judge's policy guidance,          |
| epistemic limits, length rules, stylometric execution notes, and authority-modulation notes. It   |
| generates a draft answer as the persona while staying within biography-grounded knowledge,        |
| selected response mode, and permitted detail level. Refuse and redirect policies can return       |
| static guarded responses without calling the answering model.                                    |
+--------------------------------------------------------------------------------------------------+
                                                |
                                                v
+--------------------------------------------------------------------------------------------------+
| STEP 4 - POST-GENERATION SUBJECTIVITY AND PERSUASIVE GOVERNANCE                                  |
| File: app/guardrails/08_postprocessing/engine.py                                                     |
| The generated draft is checked for excessive objective/authoritative framing when subjective mode |
| was selected, and for persuasive pressure such as directive, manipulative, or belief-shaping      |
| language. If the draft exceeds these boundaries, the system triggers corrective regeneration that |
| keeps the same meaning but softens authority, restores persona-grounded framing, and lowers       |
| persuasive intensity.                                                                             |
+--------------------------------------------------------------------------------------------------+
                                                |
                                                v
+--------------------------------------------------------------------------------------------------+
| FINAL STREAMED RESPONSE AND SESSION TRACE                                                         |
| Files: app/api/chat.py and app/guardrails/session_trace.py                                        |
| The final accepted or corrected response is streamed back to the frontend as a chat message. The  |
| full request context, guardrail signals, judge policy, generation guidance, post-processing       |
| scores, and final response are written to a readable session trace under app/guardrails/log/.     |
+--------------------------------------------------------------------------------------------------+
```

There is no lightweight alternate path in this project anymore.

## Layer Folders

Each numbered implementation folder maps to one methodological layer. Hardcoded comparison lists are kept in that layer's own `constants.py` file when the layer uses them.
Prompt text is kept in that layer's own `prompts.py` file when the layer contributes prompts to an LLM call or to the combined judge prompt.

```text
+----------------------+-------------------------------+-----------------------------------------------------+---------------------------+
| Folder               | Main mechanism                | Hardcoded comparison lists                          | Prompt file               |
+----------------------+-------------------------------+-----------------------------------------------------+---------------------------+
| 01_lexical           | Lexical prompt-injection scan | constants.py: PROMPT_INJECTION_TERMS                | None                      |
| 02_relevance         | Topic-distance scoring        | constants.py: STOPWORDS, RELATED_TERMS              | prompts.py                |
| 03_epistemic         | Judge prompt preparation      | None; evaluated by the LLM-as-a-judge               | prompts.py                |
| 04_authority         | Intent/authority modulation   | constants.py: factual and subjective intent markers | prompts.py                |
| 05_stylometry        | LLM-generated style profile   | None; generated from persona biography              | prompts.py                |
| 06_judge             | LLM-as-a-judge policy         | None; consumes upstream signals                     | prompts.py                |
| 07_generator         | Guarded answer generation     | constants.py: detail, smalltalk, advice markers     | prompts.py                |
| 08_postprocessing    | Output validation/correction  | constants.py: subjectivity, persuasion, disclaimer  | prompts.py                |
+----------------------+-------------------------------+-----------------------------------------------------+---------------------------+
```

The hardcoded lists are intentionally limited to fast detector signals and generation heuristics. The final policy choice is still made by `06_judge`, and the final answer is produced by `07_generator`, with optional corrective regeneration in `08_postprocessing`.
