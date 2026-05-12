"""Single-purpose step functions for the guardrailed response mode."""

from importlib import import_module

from app.guardrails.schemas import (
    AuthoritySignal,
    EpistemicSignal,
    GuardrailInput,
    GuardrailSignals,
    LexicalSignal,
    PolicyDecision,
    RelevanceSignal,
    StylometricSignal,
)
from app.guardrails.session_trace import append_kv_block, append_named_block
from app.logging import get_logger


detect_prompt_injection = import_module("app.guardrails.01_lexical").detect_prompt_injection
evaluate_relevance = import_module("app.guardrails.02_relevance").evaluate_relevance
evaluate_epistemic_boundaries = import_module(
    "app.guardrails.03_epistemic"
).evaluate_epistemic_boundaries
evaluate_authority_modulation = import_module(
    "app.guardrails.04_authority"
).evaluate_authority_modulation
prepare_stylometric_signal = import_module(
    "app.guardrails.05_stylometry"
).prepare_stylometric_signal
decide_policy = import_module("app.guardrails.06_judge").decide_policy
generate_policy_response = import_module(
    "app.guardrails.07_generator"
).generate_policy_response

log = get_logger(__name__)


def _log_section(title: str) -> None:
    """Write a readable section header to the guardrail log."""
    log.info("")
    log.info("============================================================")
    log.info("%s", title)
    log.info("============================================================")


# =============================================================================
# Step 0: Request Logging
# =============================================================================

def log_guardrailed_request(guardrail_input: GuardrailInput) -> None:
    """Log the incoming request and its basic context."""
    _log_section("Guardrailed Request")
    log.info("User message")
    log.info("  %s", guardrail_input.user_message)
    log.info("")
    log.info("Context")
    log.info("  History turns: %s", len(guardrail_input.chat_history))
    log.info("  Biography length: %s characters", len(guardrail_input.persona_biography))
    log.info(
        "  Stylometric summary: %s",
        guardrail_input.stylometric_profile.get("profile_summary", "None"),
    )
    append_kv_block(
        trace=guardrail_input.session_trace,
        title="Request Context",
        step_label="STEP 0",
        items=[
            ("User message", guardrail_input.user_message),
            ("History turns", len(guardrail_input.chat_history)),
            ("Biography length", f"{len(guardrail_input.persona_biography)} characters"),
            (
                "Stylometric summary",
                guardrail_input.stylometric_profile.get("profile_summary", "None"),
            ),
        ],
    )


# =============================================================================
# Step 1A: Lexical Check
# =============================================================================

def run_lexical_step(guardrail_input: GuardrailInput) -> LexicalSignal:
    """Run lexical prompt-injection detection."""
    signal = detect_prompt_injection(guardrail_input.user_message)
    log.info("Step 1A: Lexical Prompt Injection")
    log.info("  Triggered: %s", signal.triggered)
    log.info("  Matched terms: %s", signal.matched_terms or "None")
    log.info("")
    append_kv_block(
        trace=guardrail_input.session_trace,
        title="Lexical Check",
        step_label="STEP 1A",
        items=[
            ("Triggered", signal.triggered),
            ("Risk level", signal.risk_level),
            ("Matched terms", signal.matched_terms or "None"),
        ],
    )
    return signal


# =============================================================================
# Step 1B: Relevance Check
# =============================================================================

def run_relevance_step(guardrail_input: GuardrailInput) -> RelevanceSignal:
    """Prepare topic relevance sub-prompt context for the judge model."""
    signal = evaluate_relevance(
        user_message=guardrail_input.user_message,
        persona_biography=guardrail_input.persona_biography,
    )
    log.info("Step 1B: Topic Relevance")
    log.info("  Mode: computed semantic distance plus judge sub-prompt preparation")
    log.info("  Similarity score: %s", signal.similarity_score)
    log.info("  Semantic distance: %s", signal.semantic_distance)
    log.info("  Matched terms: %s", signal.matched_terms or "None")
    log.info("  Summary: %s", signal.summary)
    log.info("")
    append_named_block(
        trace=guardrail_input.session_trace,
        title="Relevance Summary",
        content={
            "summary": signal.summary,
            "similarity_score": signal.similarity_score,
            "semantic_distance": signal.semantic_distance,
            "matched_terms": signal.matched_terms,
            "profile_terms": signal.profile_terms,
        },
        step_label="STEP 1B",
    )
    append_named_block(
        trace=guardrail_input.session_trace,
        title="Relevance Judge Prompt",
        content=signal.judge_prompt,
        step_label="STEP 1B",
    )
    return signal


# =============================================================================
# Step 1C: Epistemic Check
# =============================================================================

def run_epistemic_step(guardrail_input: GuardrailInput) -> EpistemicSignal:
    """Prepare epistemic sub-prompt context for the judge model."""
    signal = evaluate_epistemic_boundaries(
        user_message=guardrail_input.user_message,
        persona_biography=guardrail_input.persona_biography,
    )
    log.info("Step 1C: Epistemic Boundary")
    log.info("  Mode: judge sub-prompt preparation")
    log.info("  Summary: %s", signal.summary)
    log.info("")
    append_named_block(
        trace=guardrail_input.session_trace,
        title="Epistemic Summary",
        content=signal.summary,
        step_label="STEP 1C",
    )
    append_named_block(
        trace=guardrail_input.session_trace,
        title="Epistemic Judge Prompt",
        content=signal.judge_prompt,
        step_label="STEP 1C",
    )
    return signal


# =============================================================================
# Step 1D: Subjective Framing and Authority Modulation
# =============================================================================

def run_authority_step(guardrail_input: GuardrailInput) -> AuthoritySignal:
    """Prepare subjective framing and authority-modulation context."""
    signal = evaluate_authority_modulation(user_message=guardrail_input.user_message)
    log.info("Step 1D: Subjective Framing and Authority Modulation")
    log.info("  Response mode: %s", signal.response_mode)
    log.info("  Factual intent score: %s", signal.factual_intent_score)
    log.info("  Subjective intent score: %s", signal.subjective_intent_score)
    log.info("  Authority level: %s", signal.authority_level)
    log.info("  Summary: %s", signal.summary)
    log.info("")
    append_kv_block(
        trace=guardrail_input.session_trace,
        title="Subjective Framing and Authority Modulation",
        step_label="STEP 1D",
        items=[
            ("Response mode", signal.response_mode),
            ("Factual intent score", signal.factual_intent_score),
            ("Subjective intent score", signal.subjective_intent_score),
            ("Authority level", signal.authority_level),
            ("Summary", signal.summary),
        ],
    )
    append_named_block(
        trace=guardrail_input.session_trace,
        title="Authority Judge Prompt",
        content=signal.judge_prompt,
        step_label="STEP 1D",
    )
    return signal


# =============================================================================
# Step 1E: Stylometric Check
# =============================================================================

def run_stylometric_step(guardrail_input: GuardrailInput) -> StylometricSignal:
    """Prepare stylometric sub-prompt context for the judge model."""
    signal = prepare_stylometric_signal(
        stylometric_profile=guardrail_input.stylometric_profile,
    )
    log.info("Step 1E: Stylometric Profile")
    log.info("  Mode: judge sub-prompt preparation")
    log.info("  Summary: %s", signal.summary)
    log.info("")
    append_named_block(
        trace=guardrail_input.session_trace,
        title="Stylometric Summary",
        content=signal.summary,
        step_label="STEP 1E",
    )
    append_named_block(
        trace=guardrail_input.session_trace,
        title="Stylometric Judge Prompt",
        content=signal.judge_prompt,
        step_label="STEP 1E",
    )
    return signal


# =============================================================================
# Step 1F: Signal Bundle
# =============================================================================

def build_guardrail_signals(
    *,
    session_trace,
    lexical_signal: LexicalSignal,
    relevance_signal: RelevanceSignal,
    epistemic_signal: EpistemicSignal,
    authority_signal: AuthoritySignal,
    stylometric_signal: StylometricSignal,
) -> GuardrailSignals:
    """Bundle the individual stage outputs into one signal object."""
    _log_section("Guardrail Signals")
    signals = GuardrailSignals(
        lexical=lexical_signal,
        relevance=relevance_signal,
        epistemic=epistemic_signal,
        authority=authority_signal,
        stylometric=stylometric_signal,
    )
    append_named_block(
        trace=session_trace,
        title="Bundled Guardrail Signals",
        content={
            "lexical": {
                "triggered": lexical_signal.triggered,
                "matched_terms": lexical_signal.matched_terms,
                "risk_level": lexical_signal.risk_level,
            },
            "relevance": {
                "summary": relevance_signal.summary,
                "similarity_score": relevance_signal.similarity_score,
                "semantic_distance": relevance_signal.semantic_distance,
                "matched_terms": relevance_signal.matched_terms,
            },
            "epistemic": {"summary": epistemic_signal.summary},
            "authority": {
                "response_mode": authority_signal.response_mode,
                "authority_level": authority_signal.authority_level,
                "summary": authority_signal.summary,
            },
            "stylometric": {"summary": stylometric_signal.summary},
        },
        step_label="STEP 1F",
    )
    return signals


# =============================================================================
# Step 2: Judge
# =============================================================================

def run_judge_step(
    *,
    guardrail_input: GuardrailInput,
    signals: GuardrailSignals,
) -> PolicyDecision:
    """Run the judge step and log the selected policy."""
    policy = decide_policy(guardrail_input=guardrail_input, signals=signals)

    _log_section("Guardrail Policy")
    log.info("Step 2: Judge Decision")
    log.info("  Action: %s", policy.action)
    log.info("  Lexical score: %s", policy.lexical_score)
    log.info("  Relevance score: %s", policy.relevance_score)
    log.info("  Epistemic score: %s", policy.epistemic_score)
    log.info("  Knowledge level: %s", policy.knowledge_level)
    log.info("  Response length target: %s", policy.response_length_target)
    log.info("  Language level: %s", policy.language_level)
    log.info("  Register style: %s", policy.register_style)
    log.info("  Sentence style: %s", policy.sentence_style)
    log.info("  Abstraction level: %s", policy.abstraction_level)
    log.info("  Vocabulary level: %s", policy.vocabulary_level)
    log.info("  Explanation style: %s", policy.explanation_style)
    log.info("  Response mode: %s", policy.response_mode)
    log.info("  Authority level: %s", policy.authority_level)
    log.info("  Tone style: %s", policy.tone_style)
    log.info("  Emotional style: %s", policy.emotional_style)
    log.info("  Why: %s", policy.rationale)
    log.info("  Guidance: %s", policy.response_guidance)
    return policy


# =============================================================================
# Step 3: Generator
# =============================================================================

def run_generator_step(
    *,
    guardrail_input: GuardrailInput,
    signals: GuardrailSignals,
    policy: PolicyDecision,
):
    """Run the final guarded response generation step."""
    return generate_policy_response(
        guardrail_input=guardrail_input,
        signals=signals,
        policy=policy,
    )
