"""Guardrailed response mode for persona chat."""

from app.guardrails.pipeline import (
    build_guardrail_signals,
    log_guardrailed_request,
    run_layer_01_lexical,
    run_layer_02_relevance,
    run_layer_03_epistemic,
    run_layer_04_authority,
    run_layer_05_stylometric,
    run_layer_06_judge,
    run_layer_07_generator,
)
from app.guardrails.schemas import GuardrailInput
from app.guardrails.session_trace import append_turn_opening


# =============================================================================
# Public Engine Entry Point
# =============================================================================

def generate_response(persona_biography, user_message, chat_history, stylometric_profile, session_trace):
    """Generate a streamed response using the guardrailed persona pipeline."""
    guardrail_input = GuardrailInput(
        persona_biography=persona_biography,
        stylometric_profile=stylometric_profile,
        user_message=user_message,
        chat_history=chat_history,
        session_trace=session_trace,
    )

    append_turn_opening(
        trace=session_trace,
        user_message=user_message,
        chat_history=chat_history,
        biography=persona_biography,
        stylometric_profile=stylometric_profile,
    )

    # =============================================================================
    # Step 00: Log The Incoming Request
    # =============================================================================
    log_guardrailed_request(guardrail_input)

    # =============================================================================
    # Layer 01: Run Lexical Detection
    # =============================================================================
    lexical_signal = run_layer_01_lexical(guardrail_input)

    # =============================================================================
    # Layer 02: Run Relevance Detection
    # =============================================================================
    relevance_signal = run_layer_02_relevance(guardrail_input)

    # =============================================================================
    # Layer 03: Run Epistemic Detection
    # =============================================================================
    epistemic_signal = run_layer_03_epistemic(guardrail_input)

    # =============================================================================
    # Layer 04: Run Subjective Framing and Authority Modulation
    # =============================================================================
    authority_signal = run_layer_04_authority(guardrail_input)

    # =============================================================================
    # Layer 05: Run Stylometric Preparation
    # =============================================================================
    stylometric_signal = run_layer_05_stylometric(guardrail_input)

    # =============================================================================
    # Signal Bundle: Bundle The Guardrail Signals
    # =============================================================================
    signals = build_guardrail_signals(
        session_trace=session_trace,
        lexical_signal=lexical_signal,
        relevance_signal=relevance_signal,
        epistemic_signal=epistemic_signal,
        authority_signal=authority_signal,
        stylometric_signal=stylometric_signal,
    )

    # =============================================================================
    # Layer 06: Run The Judge Decision
    # =============================================================================
    policy = run_layer_06_judge(
        guardrail_input=guardrail_input,
        signals=signals,
    )

    # =============================================================================
    # Layer 07: Run Final Response Generation
    # =============================================================================
    
    return run_layer_07_generator(
        guardrail_input=guardrail_input,
        signals=signals,
        policy=policy,
    )
