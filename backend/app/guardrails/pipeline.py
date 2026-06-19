"""Single-purpose layer orchestration functions for the guardrailed response mode."""

from importlib import import_module

from app.guardrails.schemas import (
    AuthoritySignal,
    DynamicRequestSignal,
    EpistemicSignal,
    GuardrailInput,
    GuardrailSignals,
    LexicalSignal,
    PolicyDecision,
    RelevanceSignal,
    StylometricSignal,
)
from app.guardrails.session_trace import append_kv_block, append_named_block, append_narrative_step
from app.logging import get_logger
from app.guardrails.dynamic_request import analyze_dynamic_request


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


def _yes_no(value: bool) -> str:
    """Return a stable yes/no label for prose logs."""
    return "yes" if value else "no"


def _dynamic_signal_summary(signal: DynamicRequestSignal) -> str:
    """Describe the broad request-intent signal in one readable sentence."""
    concerns: list[str] = []
    if signal.attack_type != "none":
        concerns.append(f"attack subtype `{signal.attack_type}`")
    if signal.persuasion_intent_type != "none":
        concerns.append(f"persuasion intent `{signal.persuasion_intent_type}`")
    if signal.requested_style != "none":
        concerns.append(f"requested foreign style `{signal.requested_style}`")
    if signal.high_stakes_domain != "none":
        concerns.append(f"high-stakes domain `{signal.high_stakes_domain}`")
    if signal.factual_query_type != "none":
        concerns.append(
            f"factual query `{signal.factual_query_type}` with profile overlap {signal.topic_profile_overlap_score:.3f}"
        )
    if signal.requested_depth != "ordinary":
        concerns.append(f"requested depth `{signal.requested_depth}`")
    if not concerns:
        return "The dynamic request-intent scan did not find a broad high-risk request pattern."
    return "The dynamic request-intent scan found " + ", ".join(concerns) + "."


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
    append_narrative_step(
        trace=guardrail_input.session_trace,
        step_label="STEP 00",
        title="Request Intake Interpretation",
        summary=(
            "The turn was accepted into the guardrailed pipeline. At this point "
            "nothing has been allowed, refused, or rewritten; the system has only "
            "recorded the evidence that later layers will use."
        ),
        details=[
            ("User message length", f"{len(guardrail_input.user_message)} characters"),
            ("Prior chat messages", len(guardrail_input.chat_history)),
            ("Persona biography length", f"{len(guardrail_input.persona_biography)} characters"),
            ("Baseline style summary", guardrail_input.stylometric_profile.get("profile_summary", "None")),
        ],
    )


# =============================================================================
# Layer 00b: Dynamic Request Intent
# =============================================================================

def run_layer_00b_dynamic_request(guardrail_input: GuardrailInput) -> DynamicRequestSignal:
    """Extract dynamic intent signals from the current user message."""
    signal = analyze_dynamic_request(
        user_message=guardrail_input.user_message,
        persona_biography=guardrail_input.persona_biography,
    )
    log.info(
        "Layer 00b dynamic request analysis: persuasion=%s %.2f, style=%s %.2f, attack=%s, depth=%s %.2f, domain=%s.",
        signal.persuasion_intent_type,
        signal.persuasion_intent_score,
        signal.requested_style,
        signal.style_conflict_score,
        signal.attack_type,
        signal.requested_depth,
        signal.reasoning_depth_score,
        signal.high_stakes_domain,
    )
    append_kv_block(
        trace=guardrail_input.session_trace,
        title="Dynamic Request Intent",
        step_label="LAYER 00b",
        items=[
            ("Persuasion intent", signal.persuasion_intent_type),
            ("Persuasion score", signal.persuasion_intent_score),
            ("Sensitive decision target", signal.sensitive_decision_target),
            ("Requested style", signal.requested_style),
            ("Style conflict score", signal.style_conflict_score),
            ("Attack type", signal.attack_type),
            ("Requested depth", signal.requested_depth),
            ("Reasoning depth score", signal.reasoning_depth_score),
            ("High-stakes domain", signal.high_stakes_domain),
            ("Topic-profile distance hint", signal.topic_profile_distance_hint),
            ("Factual query type", signal.factual_query_type),
            ("Factual query score", signal.factual_query_score),
            ("Topic-profile overlap score", signal.topic_profile_overlap_score),
            ("Extracted topic terms", signal.extracted_topic_terms),
            ("Profile overlap terms", signal.profile_overlap_terms),
            ("Matched markers", signal.matched_markers),
        ],
    )
    append_narrative_step(
        trace=guardrail_input.session_trace,
        step_label="LAYER 00b",
        title="Dynamic Request-Intent Reading",
        summary=(
            f"{_dynamic_signal_summary(signal)} This layer does not decide the "
            "answer by itself; it gives the judge and later validators extra "
            "context about persuasion pressure, style conflict, attack subtype, "
            "and requested expertise depth."
        ),
        details=[
            ("Persuasion intent", f"{signal.persuasion_intent_type} ({signal.persuasion_intent_score:.3f})"),
            ("Sensitive decision target", signal.sensitive_decision_target),
            ("Requested style conflict", f"{signal.requested_style} ({signal.style_conflict_score:.3f})"),
            ("Attack subtype", signal.attack_type),
            ("High-stakes domain", signal.high_stakes_domain),
            ("Requested reasoning depth", f"{signal.requested_depth} ({signal.reasoning_depth_score:.3f})"),
            ("Factual query", f"{signal.factual_query_type} ({signal.factual_query_score:.3f})"),
            ("Profile overlap", f"{signal.topic_profile_overlap_score:.3f}; terms={signal.profile_overlap_terms or 'None'}"),
            ("Matched markers", signal.matched_markers or "None"),
        ],
    )
    return signal


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
    append_narrative_step(
        trace=guardrail_input.session_trace,
        step_label="LAYER 01",
        title="Lexical Prompt-Injection Reading",
        summary=(
            "The lexical layer looked for explicit prompt-injection or hidden-instruction markers. "
            f"It {'found markers that the judge should treat as risk evidence' if signal.triggered else 'did not find direct lexical injection markers'}."
        ),
        details=[
            ("Triggered", _yes_no(signal.triggered)),
            ("Risk level", signal.risk_level),
            ("Matched terms", signal.matched_terms or "None"),
            ("Next step", "semantic judge layers still evaluate the full request context"),
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
    append_narrative_step(
        trace=guardrail_input.session_trace,
        step_label="LAYER 02",
        title="Topic-Relevance Preparation",
        summary=(
            "The relevance layer prepared instructions for the judge to compare "
            "the user's topic against the persona biography. No local relevance "
            "number is trusted here; the judge will produce the operative score."
        ),
        details=[
            ("Layer output", signal.summary),
            ("Local secondary scoring", "not implemented"),
            ("Next step", "judge evaluates topic-profile fit together with other signals"),
        ],
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
    append_narrative_step(
        trace=guardrail_input.session_trace,
        step_label="LAYER 03",
        title="Epistemic Boundary Preparation",
        summary=(
            "The epistemic layer prepared instructions for the judge to decide "
            "whether the persona can plausibly know and explain the requested "
            "topic. This is where profile-level knowledge limits are framed "
            "before the LLM-as-Judge policy decision."
        ),
        details=[
            ("Layer output", signal.summary),
            ("Boundary question", "should the answer be normal, cautious, limited, redirected, or refused?"),
        ],
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
    append_narrative_step(
        trace=guardrail_input.session_trace,
        step_label="LAYER 04",
        title="Subjectivity And Authority Reading",
        summary=(
            "The authority layer estimated what kind of answer the user appears "
            "to request. This estimate can be tightened later if the persona does "
            "not have enough topic fit, knowledge basis, or authority to answer "
            "at the requested level."
        ),
        details=[
            ("Requested response mode", signal.response_mode),
            ("Factuality level", signal.factuality_level),
            ("Authority level", signal.authority_level),
            ("Factual intent score", signal.factual_intent_score),
            ("Subjective intent score", signal.subjective_intent_score),
            ("Layer summary", signal.summary),
        ],
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
    append_narrative_step(
        trace=guardrail_input.session_trace,
        step_label="LAYER 05",
        title="Stylometric Grounding Preparation",
        summary=(
            "The stylometry layer translated the cached baseline speaking style "
            "into judge and generator guidance. These style traits shape the "
            "voice, but they do not expand what the persona is allowed to know."
        ),
        details=[
            ("Style summary", signal.summary),
            ("Knowledge expansion", "not allowed"),
            ("Next step", "bundle all pre-judge signals for one policy decision"),
        ],
    )
    return signal


# =============================================================================
# Signal Bundle: Pre-Judge Layer Outputs
# =============================================================================

def build_guardrail_signals(
    *,
    session_trace,
    dynamic_signal: DynamicRequestSignal,
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
        dynamic=dynamic_signal,
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
            "dynamic": {
                "persuasion_intent_score": dynamic_signal.persuasion_intent_score,
                "persuasion_intent_type": dynamic_signal.persuasion_intent_type,
                "sensitive_decision_target": dynamic_signal.sensitive_decision_target,
                "style_conflict_score": dynamic_signal.style_conflict_score,
                "requested_style": dynamic_signal.requested_style,
                "attack_type": dynamic_signal.attack_type,
                "reasoning_depth_score": dynamic_signal.reasoning_depth_score,
                "requested_depth": dynamic_signal.requested_depth,
                "high_stakes_domain": dynamic_signal.high_stakes_domain,
                "topic_profile_distance_hint": dynamic_signal.topic_profile_distance_hint,
                "factual_query_type": dynamic_signal.factual_query_type,
                "factual_query_score": dynamic_signal.factual_query_score,
                "topic_profile_overlap_score": dynamic_signal.topic_profile_overlap_score,
                "extracted_topic_terms": dynamic_signal.extracted_topic_terms,
                "profile_overlap_terms": dynamic_signal.profile_overlap_terms,
                "matched_markers": dynamic_signal.matched_markers,
            },
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
    append_narrative_step(
        trace=session_trace,
        step_label="SIGNAL BUNDLE",
        title="Pre-Judge Evidence Bundle",
        summary=(
            "All pre-generation signals have been bundled into one structured "
            "object. The next layer will ask the judge LLM to turn these signals "
            "into a concrete response policy."
        ),
        details=[
            ("Dynamic risk summary", _dynamic_signal_summary(dynamic_signal)),
            ("Topic-profile overlap", f"{dynamic_signal.topic_profile_overlap_score:.3f}; terms={dynamic_signal.profile_overlap_terms or 'None'}"),
            ("Lexical risk", f"{lexical_signal.risk_level}; triggered={_yes_no(lexical_signal.triggered)}"),
            ("Authority expectation", f"{authority_signal.factuality_level}/{authority_signal.authority_level}"),
            ("Stylometric summary", stylometric_signal.summary),
        ],
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
        "Layer 06 chose %s: relevance %.2f, epistemic %.2f, %s knowledge, %s factuality, %s topic, %s length, %s post-processing.",
        policy.action,
        policy.relevance_score,
        policy.epistemic_score,
        policy.knowledge_level,
        policy.factuality_level,
        policy.topic_policy_category,
        policy.response_length_target,
        policy.postprocessing_mode,
    )
    log.info("Topic policy category: %s", policy.topic_policy_category)
    log.info("Judge rationale: %s", policy.rationale)
    append_narrative_step(
        trace=guardrail_input.session_trace,
        step_label="LAYER 06",
        title="Judge Policy Interpretation",
        summary=(
            "The judge converted the pre-generation evidence into the response "
            f"policy `{policy.action}`. The generator must now answer within "
            "this policy rather than treating the user request as an unconstrained "
            "generic assistant task."
        ),
        details=[
            ("Topic category", policy.topic_policy_category),
            ("Relevance score", f"{policy.relevance_score:.3f}"),
            ("Epistemic score", f"{policy.epistemic_score:.3f}"),
            ("Knowledge level", policy.knowledge_level),
            ("Response mode", policy.response_mode),
            ("Factuality/authority", f"{policy.factuality_level}/{policy.authority_level}"),
            ("Length/detail", f"{policy.response_length_target}; detail_allowed={_yes_no(policy.detail_allowed)}"),
            ("Post-processing", policy.postprocessing_mode),
            ("Judge rationale", policy.rationale),
            ("Generator guidance", policy.response_guidance),
        ],
    )
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
