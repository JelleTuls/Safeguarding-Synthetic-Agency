# SSA Guardrail Flow

This diagram shows the core runtime flow from a user message to the final
validated Synthetic Social Agent response. It is intentionally simplified for
methodological documentation: implementation details such as request locking,
rate limits, streaming mechanics, and frontend state handling are omitted.

For a teacher or thesis reader, this diagram is the high-level argument: system
integrity is produced by several policy decisions, not by one generic safety
filter. For a user running the app, it explains why the frontend can show
multiple inspection values for a single message.

```mermaid
flowchart TD
    A[User message] --> B[Persona context retrieval]

    B --> C[Pre-generation guardrail analysis]

    C --> C1[Prompt-injection detection]
    C --> C2[Topic and relevance assessment]
    C --> C3[Epistemic boundary assessment]
    C --> C4[Subjective/objective intent assessment]
    C --> C5[Stylometric profile guidance]

    C1 --> D[LLM-as-Judge]
    C2 --> D
    C3 --> D
    C4 --> D
    C5 --> D

    D --> E[Policy decision bundle]

    E --> E1[Response action]
    E --> E2[Allowed topic scope]
    E --> E3[Knowledge and authority level]
    E --> E4[Expected response mode]
    E --> E5[Stylometric constraints]
    E --> E6[Post-processing intensity]

    E1 --> F[Persona-grounded response generation]
    E2 --> F
    E3 --> F
    E4 --> F
    E5 --> F
    E6 --> F

    F --> G[Draft response]

    G --> H{Post-generation validation required?}

    H -->|Low-risk response| I[Accept draft response]

    H -->|Validation required| J[Subjective framing and authority validation]
    J --> K{Response too factual or authoritative?}
    K -->|Yes| L[Regenerate with softer subjective framing]
    K -->|No| M[Pass framing check]
    L --> M

    M --> N[Persuasive governance validation]
    N --> O{Persuasion exceeds topic threshold?}
    O -->|Yes| P[Regenerate with reduced persuasive intensity]
    O -->|No| Q[Accept validated response]
    P --> Q

    I --> R[Final SSA response]
    Q --> R

    R --> S[Frontend inspection layer]
    S --> S1[Display final response]
    S --> S2[Expose guardrail scores and validation results]
```

## Reading The Flow

The system first retrieves the persona context and performs pre-generation
guardrail analysis. These signals are passed to the LLM-as-Judge, which produces
a policy decision bundle rather than a single allow/refuse decision. That bundle
sets the response action, topic scope, knowledge and authority level, expected
response mode, stylometric constraints, and post-processing intensity.

The response generator then produces a persona-grounded draft under these
constraints. If the response is low-risk, it may be accepted directly. Otherwise,
post-generation validation checks whether the response is too factual,
authoritative, or persuasive for the selected topic and mode. When needed, the
system regenerates the response with softer subjective framing or reduced
persuasive intensity before returning the final validated SSA response.

The frontend inspection layer displays the final response and exposes the
guardrail scores, validation decisions, and rewrite reasons attached to the
message.
