# Guardrailed Flow

Every persona chat message uses this flow.

```text
chat_flow.py
  -> guardrails/engine.py
  -> pipeline.py
       Step 0: request logging
       Step 1A: lexical prompt-injection scan
       Step 1B: relevance preparation
       Step 1C: epistemic-boundary preparation
       Step 1D: stylometric preparation
       Step 1E: signal bundling
       Step 2: judge policy decision
       Step 3: guarded response generation
  -> streamed response
  -> readable session trace in guardrails/log/
```

There is no lightweight alternate path in this project anymore.
