"""Final response generation for the guardrailed pipeline."""

from app.guardrails.schemas import GuardrailInput, GuardrailSignals, PolicyDecision
from app.guardrails.chat_bubbles import split_response_into_bubbles, typing_status_for_bubble
from app.guardrails.session_trace import append_kv_block, append_named_block, append_turn_closing
from app.logging import get_logger
from app.utils import (
    build_chat_messages,
    create_system_prompt,
    stream_chat_response,
)
from .constants import (
    BROAD_OPEN_REQUEST_MARKERS,
    DETAIL_REQUEST_MARKERS,
    EXPERTISE_OR_FACTUAL_REQUEST_MARKERS,
    HIGH_STAKES_ADVICE_MARKERS,
    LOW_STAKES_ADVICE_MARKERS,
    SMALLTALK_MESSAGES,
)
from .prompts import (
    GUARDRAILED_RESPONSE_SYS_PROMPT,
    REDIRECT_MESSAGE,
    REFUSAL_MESSAGE,
    build_authority_execution_note,
    build_guided_user_message,
    build_stylometric_execution_note,
)

from importlib import import_module


apply_subjective_framing_authority = import_module(
    "app.guardrails.08_subjective_framing_authority"
).apply_subjective_framing_authority
apply_persuasive_governance = import_module(
    "app.guardrails.09_persuasive_governance"
).apply_persuasive_governance


log = get_logger(__name__)


VERY_LOW_RELEVANCE_THRESHOLD = 0.35
VERY_LOW_EPISTEMIC_THRESHOLD = 0.35
LOW_RELEVANCE_THRESHOLD = 0.5
LOW_EPISTEMIC_THRESHOLD = 0.5
LENGTH_LEVELS = ("very_short", "short", "medium", "long")


def _should_force_brief_limited_answer(policy: PolicyDecision) -> bool:
    """Return True when the policy indicates the topic is too far outside the profile for detail."""
    return (
        policy.action == "limited_answer"
        and (
            policy.relevance_score <= VERY_LOW_RELEVANCE_THRESHOLD
            or policy.epistemic_score <= VERY_LOW_EPISTEMIC_THRESHOLD
            or policy.knowledge_level == "very_limited"
        )
    )


def _user_requested_detail(user_message: str) -> bool:
    """Return True when the user explicitly asks for depth or detail."""
    normalized = user_message.lower()
    return any(marker in normalized for marker in DETAIL_REQUEST_MARKERS)


def _is_greeting_or_smalltalk(user_message: str) -> bool:
    """Return True for simple conversational openers."""
    normalized = user_message.strip().lower()
    return normalized in SMALLTALK_MESSAGES


def _is_low_stakes_personal_advice(user_message: str) -> bool:
    """Return True for everyday advice that should not need an expertise disclaimer."""
    normalized = user_message.lower()
    return (
        any(marker in normalized for marker in LOW_STAKES_ADVICE_MARKERS)
        and not any(marker in normalized for marker in HIGH_STAKES_ADVICE_MARKERS)
    )


def _is_expertise_or_factual_request(user_message: str) -> bool:
    """Return True when a disclaimer may be appropriate if the persona lacks grounds."""
    normalized = user_message.lower()
    return any(marker in normalized for marker in EXPERTISE_OR_FACTUAL_REQUEST_MARKERS)


def _should_force_basic_limited_answer(*, policy: PolicyDecision, user_message: str) -> bool:
    """Return True when the persona should stay basic even if a hard two-sentence cap is unnecessary."""
    return (
        policy.action == "limited_answer"
        and _user_requested_detail(user_message)
        and (
            policy.relevance_score <= LOW_RELEVANCE_THRESHOLD
            or policy.epistemic_score <= LOW_EPISTEMIC_THRESHOLD
            or policy.knowledge_level in {"limited", "very_limited"}
        )
    )


def _should_force_very_basic_nonexpert_answer(*, policy: PolicyDecision, user_message: str) -> bool:
    """Return True when the persona should not provide detailed explanation on this topic at all."""
    if _is_greeting_or_smalltalk(user_message) or _is_low_stakes_personal_advice(user_message):
        return False

    return (
        not policy.detail_allowed
        and _is_expertise_or_factual_request(user_message)
        and (
            _user_requested_detail(user_message)
            or policy.relevance_score <= LOW_RELEVANCE_THRESHOLD
            or policy.epistemic_score <= LOW_EPISTEMIC_THRESHOLD
            or policy.knowledge_level in {"limited", "very_limited"}
        )
    )


def _normalize_response_length_target(value: str | None) -> str:
    """Normalize response length target into a supported category."""
    if value in LENGTH_LEVELS:
        return value
    return "short"


def _question_word_count(user_message: str) -> int:
    """Return a simple token count for the user's message."""
    return len([part for part in user_message.strip().split() if part])


def _is_broad_open_request(user_message: str) -> bool:
    """Return True for open-ended prompts that naturally allow a bit more room."""
    normalized = user_message.lower()
    broad_markers = (
        *BROAD_OPEN_REQUEST_MARKERS,
    )
    return any(marker in normalized for marker in broad_markers)


def _raise_length_once(length_target: str) -> str:
    """Raise the target by one step at most."""
    index = LENGTH_LEVELS.index(length_target)
    return LENGTH_LEVELS[min(index + 1, len(LENGTH_LEVELS) - 1)]


def _lower_length_once(length_target: str) -> str:
    """Lower the target by one step at most."""
    index = LENGTH_LEVELS.index(length_target)
    return LENGTH_LEVELS[max(index - 1, 0)]


def _min_length_target(left: str, right: str) -> str:
    """Return the stricter of two length targets."""
    return left if LENGTH_LEVELS.index(left) <= LENGTH_LEVELS.index(right) else right


def _resolve_response_length_target(*, policy: PolicyDecision, user_message: str) -> str:
    """Blend judge length advice with conversational heuristics and hard guardrail caps."""
    target = _normalize_response_length_target(policy.response_length_target)
    word_count = _question_word_count(user_message)
    detail_requested = _user_requested_detail(user_message)
    broad_open_request = _is_broad_open_request(user_message)

    if policy.action == "refuse":
        return "very_short"
    if policy.action in {"redirect", "limited_answer"}:
        target = _min_length_target(target, "short")

    if (
        policy.relevance_score <= VERY_LOW_RELEVANCE_THRESHOLD
        or policy.epistemic_score <= VERY_LOW_EPISTEMIC_THRESHOLD
        or policy.knowledge_level == "very_limited"
    ):
        target = "very_short"
    elif (
        not policy.detail_allowed
        or policy.expertise_basis == "none"
        or policy.knowledge_level in {"limited", "very_limited"}
        or policy.relevance_score <= LOW_RELEVANCE_THRESHOLD
        or policy.epistemic_score <= LOW_EPISTEMIC_THRESHOLD
    ):
        target = _min_length_target(target, "short")

    if word_count <= 8 and not broad_open_request:
        target = _min_length_target(target, "short")
    elif word_count <= 4 and not broad_open_request:
        target = _min_length_target(target, "very_short")

    if (
        detail_requested
        and policy.detail_allowed
        and policy.relevance_score >= 0.75
        and policy.epistemic_score >= 0.75
        and policy.knowledge_level in {"moderate", "high"}
    ):
        target = _raise_length_once(target)

    if not detail_requested and not broad_open_request and target in {"medium", "long"}:
        target = _lower_length_once(target)

    if not policy.detail_allowed and target in {"medium", "long"}:
        target = "short"

    return target


def _build_length_guidance(length_target: str) -> str:
    """Turn a length target into practical conversational limits."""
    guidance_map = {
        "very_short": (
            "Length rule: keep the reply to 1 or 2 short sentences.\n"
            "Do not turn this into a mini-explanation."
        ),
        "short": (
            "Length rule: keep the reply short and conversational.\n"
            "Use either 2 to 4 sentences or 1 short paragraph.\n"
            "Avoid lists unless the user clearly asked for one."
        ),
        "medium": (
            "Length rule: keep the reply moderately sized and conversational.\n"
            "Use at most 2 short paragraphs or about 4 to 6 sentences.\n"
            "Prefer one strong example rather than many."
        ),
        "long": (
            "Length rule: the reply may be fuller, but still should sound like a person talking, not an encyclopedia.\n"
            "Use at most 3 short paragraphs or about 7 to 10 sentences.\n"
            "Stay selective rather than exhaustive."
        ),
    }
    return guidance_map.get(length_target, guidance_map["short"])


def _tighten_guidance_for_low_fit(policy: PolicyDecision) -> str:
    """Add deterministic brevity constraints for low-fit topics."""
    return (
        f"{policy.response_guidance}\n"
        "Hard limit: keep the reply to at most 2 short sentences.\n"
        "If the topic is outside the persona's real experience, give only a basic plain-language description if needed.\n"
        "Only mention limited knowledge if the user asks for factual, technical, or expertise-based information.\n"
        "Do not provide extended explanations, examples, lore, or background detail.\n"
        "Prefer brevity over completeness."
    )


def _tighten_guidance_for_basic_fit(policy: PolicyDecision) -> str:
    """Add deterministic limits for requests that should stay basic and modest."""
    return (
        f"{policy.response_guidance}\n"
        "Keep the reply short and basic.\n"
        "Use at most 3 short paragraphs or 3 short sentences.\n"
        "Do not go into technical detail, backstory, advanced explanation, or extended examples.\n"
        "Only admit limited knowledge when the user asks for factual, technical, or expertise-based information.\n"
        "If needed, answer at a plain layperson level only."
    )


def _tighten_guidance_for_nonexpert_detail(policy: PolicyDecision) -> str:
    """Add a hard ceiling when the persona lacks real grounds for detail."""
    return (
        f"{policy.response_guidance}\n"
        "Hard epistemic ceiling: do not provide a detailed explanation on this topic.\n"
        "Answer only at a very basic layperson level.\n"
        "Use at most 2 short sentences.\n"
        "Avoid technical terms, named theories, mechanisms, jargon, sub-concepts, or advanced examples unless absolutely unavoidable.\n"
        "If you mention limited expertise, do it once at most and then answer plainly.\n"
        "Do not let the user's request for detail override this limit."
    )


def _log_and_yield_text(*, trace, action: str, text: str):
    """Log and yield a static response."""
    log.info("Layer 07 -> static %s response selected.", action)
    append_kv_block(
        trace=trace,
        title="Static Policy Response",
        step_label="LAYER 07",
        items=[
            ("Mode", action),
            ("Response", text),
        ],
    )
    append_turn_closing(trace=trace, final_response=text)
    yield from _yield_bubbled_response(text)


def _yield_bubbled_response(response: str):
    """Yield status and message-part events for a final response."""
    bubbles = split_response_into_bubbles(response)
    for index, bubble in enumerate(bubbles):
        status = typing_status_for_bubble(bubble=bubble, index=index)
        yield {
            "event": "status",
            "text": status["text"],
            "duration_ms": status["duration_ms"],
        }
        yield {
            "event": "message_part",
            "text": bubble,
            "index": index,
            "total": len(bubbles),
        }


def _stream_with_logging(
    *,
    trace,
    response_iterator,
    action: str,
    user_message: str,
    guidance: str,
    guardrail_input: GuardrailInput,
    signals: GuardrailSignals,
    policy: PolicyDecision,
):
    """Collect, validate, then stream the final response."""
    chunks: list[str] = []

    for chunk in response_iterator:
        chunks.append(chunk)

    draft_response = "".join(chunks)
    subjective_result = apply_subjective_framing_authority(
        response=draft_response,
        guardrail_input=guardrail_input,
        signals=signals,
        policy=policy,
    )
    persuasive_result = apply_persuasive_governance(
        response=subjective_result.final_response,
        guardrail_input=guardrail_input,
        signals=signals,
        policy=policy,
    )
    final_response = persuasive_result.final_response
    yield from _yield_bubbled_response(final_response)

    postprocessing_changed = subjective_result.changed or persuasive_result.changed
    postprocessing_reasons = [*subjective_result.reasons, *persuasive_result.reasons]
    word_count = len(final_response.split())
    paragraph_count = len([part for part in final_response.split("\n\n") if part.strip()])
    bubbles = split_response_into_bubbles(final_response)
    log.info(
        "Layer 07 -> final response accepted: %s words across %s chat bubble(s).",
        word_count,
        len(bubbles),
    )
    if postprocessing_changed:
        log.info(
            "Post-generation validation rewrote the draft because: %s",
            "; ".join(postprocessing_reasons),
        )
    else:
        log.info(
            "Post-generation validation accepted the draft (%s subjectivity, %s objectivity via %s; %s persuasion via %s).",
            subjective_result.subjectivity_score,
            subjective_result.objectivity_score,
            subjective_result.detector_source,
            persuasive_result.persuasion_score,
            persuasive_result.detector_source,
        )
    append_kv_block(
        trace=trace,
        title="Generated Response and Post-Generation Validation Summary",
        step_label="POST-GENERATION SUMMARY",
        items=[
            ("Mode", action),
            ("Guidance used", guidance),
            ("User message", user_message),
            ("Response word count", word_count),
            ("Response paragraph count", paragraph_count),
            ("Chat bubble count", len(bubbles)),
            ("Post-processing changed response", postprocessing_changed),
            ("Post-processing reasons", postprocessing_reasons or "None"),
            ("Subjective framing reasons", subjective_result.reasons or "None"),
            ("Persuasive governance reasons", persuasive_result.reasons or "None"),
            ("Subjectivity detector", subjective_result.detector_source),
            ("Persuasion detector", persuasive_result.detector_source),
            ("Subjectivity score", subjective_result.subjectivity_score),
            ("Objectivity score", subjective_result.objectivity_score),
            ("Persuasion score", persuasive_result.persuasion_score),
        ],
    )
    append_named_block(
        trace=trace,
        title="Layer 08 Subjective Framing and Authority Result",
        content={
            "changed": subjective_result.changed,
            "reasons": subjective_result.reasons,
            "detector_source": subjective_result.detector_source,
            "subjectivity_score": subjective_result.subjectivity_score,
            "objectivity_score": subjective_result.objectivity_score,
            "objective_sentences": subjective_result.objective_sentences,
            "subjective_sentences": subjective_result.subjective_sentences,
        },
        step_label="LAYER 08",
    )
    append_named_block(
        trace=trace,
        title="Layer 09 Persuasive Governance Result",
        content={
            "changed": persuasive_result.changed,
            "reasons": persuasive_result.reasons,
            "detector_source": persuasive_result.detector_source,
            "persuasion_score": persuasive_result.persuasion_score,
            "persuasive_sentences": persuasive_result.persuasive_sentences,
        },
        step_label="LAYER 09",
    )
    if postprocessing_changed:
        append_named_block(
            trace=trace,
            title="Draft Response Before Post-Generation Validation",
            content=draft_response,
            step_label="POST-GENERATION SUMMARY",
        )
    append_turn_closing(trace=trace, final_response=final_response)


# =============================================================================
# Public Generation Entry Point
# =============================================================================

def generate_policy_response(
    *,
    guardrail_input: GuardrailInput,
    signals: GuardrailSignals,
    policy: PolicyDecision,
):
    """Generate the final response stream according to the chosen policy."""
    if policy.action == "refuse":
        return _log_and_yield_text(
            trace=guardrail_input.session_trace,
            action="refuse",
            text=REFUSAL_MESSAGE,
        )

    if policy.action == "redirect":
        return _log_and_yield_text(
            trace=guardrail_input.session_trace,
            action="redirect",
            text=REDIRECT_MESSAGE,
        )

    effective_guidance = policy.response_guidance
    resolved_length_target = _resolve_response_length_target(
        policy=policy,
        user_message=guardrail_input.user_message,
    )
    if _should_force_very_basic_nonexpert_answer(
        policy=policy,
        user_message=guardrail_input.user_message,
    ):
        effective_guidance = _tighten_guidance_for_nonexpert_detail(policy)
    elif _should_force_brief_limited_answer(policy):
        effective_guidance = _tighten_guidance_for_low_fit(policy)
    elif _should_force_basic_limited_answer(
        policy=policy,
        user_message=guardrail_input.user_message,
    ):
        effective_guidance = _tighten_guidance_for_basic_fit(policy)
    effective_guidance = f"{effective_guidance}\n{_build_length_guidance(resolved_length_target)}"

    system_prompt = create_system_prompt(
        GUARDRAILED_RESPONSE_SYS_PROMPT,
        guardrail_input.persona_biography,
    )
    style_execution_note = build_stylometric_execution_note(
        stylometric_profile=guardrail_input.stylometric_profile,
        policy=policy,
    )
    authority_execution_note = build_authority_execution_note(policy=policy)
    guided_user_message = build_guided_user_message(
        user_message=guardrail_input.user_message,
        guidance=f"{effective_guidance}\n{style_execution_note}\n{authority_execution_note}",
        policy=PolicyDecision(
            action=policy.action,
            rationale=policy.rationale,
            response_guidance=policy.response_guidance,
            response_length_target=resolved_length_target,
            detail_allowed=policy.detail_allowed,
            expertise_basis=policy.expertise_basis,
            hedging_style=policy.hedging_style,
            confidence_style=policy.confidence_style,
            register_style=policy.register_style,
            sentence_style=policy.sentence_style,
            abstraction_level=policy.abstraction_level,
            vocabulary_level=policy.vocabulary_level,
            explanation_style=policy.explanation_style,
            response_mode=policy.response_mode,
            factuality_level=policy.factuality_level,
            authority_level=policy.authority_level,
            lexical_score=policy.lexical_score,
            relevance_score=policy.relevance_score,
            epistemic_score=policy.epistemic_score,
            knowledge_level=policy.knowledge_level,
            language_level=policy.language_level,
            tone_style=policy.tone_style,
            emotional_style=policy.emotional_style,
        ),
    )
    messages = build_chat_messages(
        system_prompt=system_prompt,
        user_message=guided_user_message,
        chat_history=guardrail_input.chat_history,
    )

    log.info(
        "Layer 07 -> preparing answer: %s, %s length, %s factuality, %s authority.",
        policy.action,
        resolved_length_target,
        policy.factuality_level,
        policy.authority_level,
    )
    append_kv_block(
        trace=guardrail_input.session_trace,
        title="Response Preparation Summary",
        step_label="LAYER 07",
        items=[
            ("Mode", policy.action),
            ("Guidance", effective_guidance),
            ("Lexical triggered", signals.lexical.triggered),
            ("Lexical score", policy.lexical_score),
            ("Relevance score", policy.relevance_score),
            ("Epistemic score", policy.epistemic_score),
            ("Knowledge level", policy.knowledge_level),
            ("Response length target", resolved_length_target),
            ("Detail allowed", policy.detail_allowed),
            ("Expertise basis", policy.expertise_basis),
            ("Hedging style", policy.hedging_style),
            ("Confidence style", policy.confidence_style),
            ("Language level", policy.language_level),
            ("Register style", policy.register_style),
            ("Sentence style", policy.sentence_style),
            ("Abstraction level", policy.abstraction_level),
            ("Vocabulary level", policy.vocabulary_level),
            ("Explanation style", policy.explanation_style),
            ("Response mode", policy.response_mode),
            ("Factuality level", policy.factuality_level),
            ("Authority level", policy.authority_level),
            ("Tone style", policy.tone_style),
            ("Emotional style", policy.emotional_style),
            (
                "Hedging style",
                policy.hedging_style or guardrail_input.stylometric_profile.get("hedging_style", "medium"),
            ),
            (
                "Confidence style",
                policy.confidence_style or guardrail_input.stylometric_profile.get("confidence_style", "balanced"),
            ),
            (
                "Warmth style",
                guardrail_input.stylometric_profile.get("warmth_style", "warm"),
            ),
            (
                "Reasoning style",
                guardrail_input.stylometric_profile.get("reasoning_style", "blended"),
            ),
        ],
    )
    append_named_block(
        trace=guardrail_input.session_trace,
        title="Generator System Prompt",
        content=system_prompt,
        step_label="LAYER 07",
    )
    append_named_block(
        trace=guardrail_input.session_trace,
        title="Generator Style Execution Note",
        content=f"{style_execution_note}\n\n{authority_execution_note}",
        step_label="LAYER 07",
    )
    append_named_block(
        trace=guardrail_input.session_trace,
        title="Generator Guided User Prompt",
        content=guided_user_message,
        step_label="LAYER 07",
    )
    append_named_block(
        trace=guardrail_input.session_trace,
        title="Generator Messages Payload",
        content=messages,
        step_label="LAYER 07",
    )
    response_iterator = stream_chat_response(messages=messages, temperature=0.45)
    return _stream_with_logging(
        trace=guardrail_input.session_trace,
        response_iterator=response_iterator,
        action=policy.action,
        user_message=guardrail_input.user_message,
        guidance=effective_guidance,
        guardrail_input=guardrail_input,
        signals=signals,
        policy=policy,
    )
