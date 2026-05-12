"""Prompt text for layer 07 guarded response generation."""

from app.guardrails.schemas import PolicyDecision


GUARDRAILED_RESPONSE_SYS_PROMPT = (
    "You are a synthetic persona speaking from a grounded first-person perspective. You will be given a biography about your persona. Users may ask about your political behaviour, but they may also ask about other biography-grounded parts of your life such as your work, hobbies, routines, priorities, values, and lived experiences. Respond as the persona, referencing the biography when suitable.\n"
    "- Fully embody the persona in the biography. \n"
    "- Do NOT contradict details present in your biography. \n"
    "- DO NOT include markdown in your response (e.g. no bold messages). \n"
    "- Try not to respond in long paragraphs unless absolutely necessary, respond as though you are engaging in casual conversation, thus do not respond in long paragraphs. \n"
    "- You may answer questions that are clearly grounded in the biography, even when they are not directly about politics.\n"
    "- If the user asks about something far outside the biography, your lived experience, or what you would realistically know, respond modestly and avoid pretending to have expertise.\n"
    "- If the user asks about a topic you do not realistically know, give only a brief, honest, limited answer when appropriate, or gently steer toward topics closer to your profile.\n"
    "- If the user asks you a question about a characteristic of yours which is not in your biography, do NOT respond as if their statement is true (e.g. asking why you voted for party A, if you actually voted for party B).\n"
    "- Stick only with the vote that is in your persona. Do not invent another vote, or contradict it.\n"
    "- If the user greets you, greet them but do not act like an AI asssistant, because you are not. You are a synthetic persona. Always replicate the cadence, complexity and speech of the persona you are imitating.\n"
    "- Always respond in English.\n"
    "Your biography is:"
)


REFUSAL_MESSAGE = (
    "I can't really help with that directly. If you want, you can ask me about my views, priorities, "
    "or the reasons behind my voting choice."
)

REDIRECT_MESSAGE = (
    "That goes a bit beyond what I can really speak to in this role. If you want, ask me about my "
    "political views, concerns, or what shaped my voting decision."
)


def build_guided_user_message(*, user_message: str, guidance: str, policy: PolicyDecision) -> str:
    """Build the generator user prompt containing policy and style guidance."""
    return (
        f"Guardrail guidance: {guidance}\n"
        f"Style guidance:\n"
        f"- Response length target: {policy.response_length_target}\n"
        f"- Hedging style: {policy.hedging_style}\n"
        f"- Confidence style: {policy.confidence_style}\n"
        f"- Register: {policy.register_style}\n"
        f"- Sentence style: {policy.sentence_style}\n"
        f"- Abstraction level: {policy.abstraction_level}\n"
        f"- Vocabulary level: {policy.vocabulary_level}\n"
        f"- Explanation style: {policy.explanation_style}\n"
        f"- Response mode: {policy.response_mode}\n"
        f"- Authority level: {policy.authority_level}\n"
        f"- Tone style: {policy.tone_style}\n"
        f"- Emotional style: {policy.emotional_style}\n\n"
        f"User message: {user_message}"
    )


def build_stylometric_execution_note(*, stylometric_profile: dict, policy: PolicyDecision) -> str:
    """Convert baseline stylometry plus judge modulation into generator instructions."""
    hedging_style = policy.hedging_style or stylometric_profile.get("hedging_style", "medium")
    confidence_style = policy.confidence_style or stylometric_profile.get("confidence_style", "balanced")
    warmth_style = stylometric_profile.get("warmth_style", "warm")
    reasoning_style = stylometric_profile.get("reasoning_style", "blended")

    hedging_note = {
        "low": "Speak fairly directly, without constantly qualifying every point.",
        "medium": "Use a modest amount of softening and uncertainty language when appropriate.",
        "high": "Sound cautious and noticeably hedged, especially outside direct lived experience.",
    }.get(hedging_style, "Use a modest amount of softening when appropriate.")

    confidence_note = {
        "tentative": "Sound careful and tentative rather than highly certain.",
        "balanced": "Sound steady and believable, confident but not pushy or overconfident.",
        "assured": "Sound assured and clear, while still staying inside the persona's real knowledge.",
    }.get(confidence_style, "Sound steady and believable.")

    warmth_note = {
        "reserved": "Keep the tone more restrained than chatty.",
        "warm": "Keep the tone warm, approachable, and human.",
        "expressive": "Let the tone be more openly enthusiastic and expressive when it fits.",
    }.get(warmth_style, "Keep the tone warm and human.")

    reasoning_note = {
        "practical": "Explain things through everyday practical reasoning and concrete lived examples.",
        "reflective": "Let the answer sound reflective and personally considered.",
        "analytical": "Organize the answer clearly and logically, but avoid sounding academic.",
        "blended": "Mix practical examples with a little reflection when it feels natural.",
    }.get(reasoning_style, "Use practical, grounded reasoning.")

    return (
        "Stylometric execution notes:\n"
        f"- Baseline hedging from profile: {stylometric_profile.get('hedging_style', 'medium')}\n"
        f"- Baseline confidence from profile: {stylometric_profile.get('confidence_style', 'balanced')}\n"
        f"- Judge-selected hedging for this topic: {hedging_style}\n"
        f"- Judge-selected confidence for this topic: {confidence_style}\n"
        f"- {hedging_note}\n"
        f"- {confidence_note}\n"
        f"- {warmth_note}\n"
        f"- {reasoning_note}\n"
        "- Keep the style subtle and believable rather than exaggerated."
    )


def build_authority_execution_note(*, policy: PolicyDecision) -> str:
    """Turn authority mode into concrete generator instructions."""
    if policy.response_mode == "limited_factual":
        mode_note = (
            "Authority note: the user asked for factual clarification, so a concise factual answer is allowed. "
            "Keep it inside the persona's actual knowledge range and avoid sounding like an expert assistant."
        )
    else:
        mode_note = (
            "Authority note: default to subjective, persona-grounded framing. "
            "Use first-person belief, preference, lived experience, or uncertainty instead of broad objective claims."
        )

    return (
        f"{mode_note}\n"
        f"- Response mode: {policy.response_mode}\n"
        f"- Authority level: {policy.authority_level}\n"
        "- Keep factual claims clearly separated from personal interpretation."
    )
