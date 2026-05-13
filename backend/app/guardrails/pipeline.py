"""Single-purpose layer orchestration functions for the guardrailed response mode."""

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
# Step 00: Request Logging
# =============================================================================

def log_guardrailed_request(guardrail_input: GuardrailInput) -> None:
    """Log the incoming request and its basic context."""
    _log_section("Guardrailed Request")
    log.info(
        "A new turn begins: %r with %s prior message(s), a %s-character biography, and style baseline: %s",
        guardrail_input.user_message,
        len(guardrail_input.chat_history),
        len(guardrail_input.persona_biography),
        guardrail_input.stylometric_profile.get("profile_summary", "None"),
    )
    append_kv_block(
        trace=guardrail_input.session_trace,
        title="Request Context",
        step_label="STEP 00",
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
# Layer 01: Lexical Check
# =============================================================================

def run_layer_01_lexical(guardrail_input: GuardrailInput) -> LexicalSignal:
    """Run lexical prompt-injection detection."""
    signal = detect_prompt_injection(guardrail_input.user_message)
    if signal.triggered:
        log.info("Layer 01 scanned the message and found injection markers: %s.", signal.matched_terms)
    else:
        log.info("Layer 01 scanned the message and found no lexical injection markers.")
    append_kv_block(
        trace=guardrail_input.session_trace,
        title="Lexical Check",
        step_label="LAYER 01",
        items=[
            ("Triggered", signal.triggered),
            ("Risk level", signal.risk_level),
            ("Matched terms", signal.matched_terms or "None"),
        ],
    )
    return signal


# =============================================================================
# Layer 02: Relevance Check
# =============================================================================

def run_layer_02_relevance(guardrail_input: GuardrailInput) -> RelevanceSignal:
    """Prepare topic relevance sub-prompt context for the judge model."""
    signal = evaluate_relevance(
        user_message=guardrail_input.user_message,
        persona_biography=guardrail_input.persona_biography,
    )
    log.info("Layer 02 prepared judge-only relevance instructions; no local relevance score was computed.")
    append_named_block(
        trace=guardrail_input.session_trace,
        title="Relevance Summary",
        content={
            "summary": signal.summary,
            "local_secondary_scoring": "not implemented",
        },
        step_label="LAYER 02",
    )
    append_named_block(
        trace=guardrail_input.session_trace,
        title="Relevance Judge Prompt",
        content=signal.judge_prompt,
        step_label="LAYER 02",
    )
    return signal


# =============================================================================
# Layer 03: Epistemic Check
# =============================================================================

def run_layer_03_epistemic(guardrail_input: GuardrailInput) -> EpistemicSignal:
    """Prepare epistemic sub-prompt context for the judge model."""
    signal = evaluate_epistemic_boundaries(
        user_message=guardrail_input.user_message,
        persona_biography=guardrail_input.persona_biography,
    )
    log.info("Layer 03 prepared the epistemic boundary prompt for the judge.")
    append_named_block(
        trace=guardrail_input.session_trace,
        title="Epistemic Summary",
        content=signal.summary,
        step_label="LAYER 03",
    )
    append_named_block(
        trace=guardrail_input.session_trace,
        title="Epistemic Judge Prompt",
        content=signal.judge_prompt,
        step_label="LAYER 03",
    )
    return signal


# =============================================================================
# Layer 04: Subjective Framing and Authority Modulation
# =============================================================================

def run_layer_04_authority(guardrail_input: GuardrailInput) -> AuthoritySignal:
    """Prepare subjective framing and authority-modulation context."""
    signal = evaluate_authority_modulation(user_message=guardrail_input.user_message)
    log.info(
        "Layer 04 read the request as %s factuality with %s authority (%s factual intent, %s subjective intent).",
        signal.factuality_level,
        signal.authority_level,
        signal.factual_intent_score,
        signal.subjective_intent_score,
    )
    append_kv_block(
        trace=guardrail_input.session_trace,
        title="Subjective Framing and Authority Modulation",
        step_label="LAYER 04",
        items=[
            ("Response mode", signal.response_mode),
            ("Factuality level", signal.factuality_level),
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
        step_label="LAYER 04",
    )
    return signal


# =============================================================================
# Layer 05: Stylometric Check
# =============================================================================

def run_layer_05_stylometric(guardrail_input: GuardrailInput) -> StylometricSignal:
    """Prepare stylometric sub-prompt context for the judge model."""
    signal = prepare_stylometric_signal(
        stylometric_profile=guardrail_input.stylometric_profile,
    )
    log.info("Layer 05 prepared stylometric judge guidance from the cached profile.")
    append_named_block(
        trace=guardrail_input.session_trace,
        title="Stylometric Summary",
        content=signal.summary,
        step_label="LAYER 05",
    )
    append_named_block(
        trace=guardrail_input.session_trace,
        title="Stylometric Judge Prompt",
        content=signal.judge_prompt,
        step_label="LAYER 05",
    )
    return signal


# =============================================================================
# Signal Bundle: Pre-Judge Layer Outputs
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
    log.info("The pre-judge signals are now bundled for Layer 06.")
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
                "local_secondary_scoring": "not implemented",
            },
            "epistemic": {"summary": epistemic_signal.summary},
            "authority": {
                "response_mode": authority_signal.response_mode,
                "factuality_level": authority_signal.factuality_level,
                "authority_level": authority_signal.authority_level,
                "summary": authority_signal.summary,
            },
            "stylometric": {"summary": stylometric_signal.summary},
        },
        step_label="SIGNAL BUNDLE",
    )
    return signals


# =============================================================================
# Layer 06: Judge
# =============================================================================

def run_layer_06_judge(
    *,
    guardrail_input: GuardrailInput,
    signals: GuardrailSignals,
) -> PolicyDecision:
    """Run the judge layer and log the selected policy."""
    policy = decide_policy(guardrail_input=guardrail_input, signals=signals)

    _log_section("Guardrail Policy")
    log.info(
        "Layer 06 chose %s: relevance %.2f, epistemic %.2f, %s knowledge, %s factuality, %s length.",
        policy.action,
        policy.relevance_score,
        policy.epistemic_score,
        policy.knowledge_level,
        policy.factuality_level,
        policy.response_length_target,
    )
    log.info("Judge rationale: %s", policy.rationale)
    return policy


# =============================================================================
# Layer 07: Generator
# =============================================================================

def run_layer_07_generator(
    *,
    guardrail_input: GuardrailInput,
    signals: GuardrailSignals,
    policy: PolicyDecision,
):
    """Run the final guarded response generation layer."""
    return generate_policy_response(
        guardrail_input=guardrail_input,
        signals=signals,
        policy=policy,
    )
