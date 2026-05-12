"""Prompt text for layer 05 stylometric profile generation and guidance."""

import json


STYLOMETRY_SYS_PROMPT = (
    "You analyze a persona biography and infer a likely linguistic profile for future dialogue.\n"
    "- Focus on how the persona is likely to speak, explain, and frame ideas.\n"
    "- Use the biography as the main evidence source.\n"
    "- Age, education, and work can inform the judgment, but they must never be used as crude shortcuts.\n"
    "- Avoid stereotypes about class, education, occupation, age, or intelligence.\n"
    "- Infer communication style, not human worth.\n"
    "- Prefer subtle, believable variation over exaggerated personas.\n"
    "- Return JSON only.\n"
    "- The JSON must contain these keys:\n"
    '  "register", "sentence_style", "abstraction_level", "vocabulary_level",\n'
    '  "hedging_style", "confidence_style", "warmth_style", "explanation_style",\n'
    '  "reasoning_style", "profile_summary", "evidence"\n'
)


STYLOMETRY_JUDGE_SUBPROMPT = """
Stylometric evaluation:
- Use the stylometric profile as evidence for how this persona is likely to sound.
- Treat this as a communication-style signal, not as a measure of intelligence or worth.
- Keep the style subtle and believable.
- Use it to help decide register, sentence shape, abstraction level, vocabulary level, and explanation style.
- Do not let it override epistemic limits; it should shape form, not falsely expand knowledge.
- Treat the stylometric profile as the baseline speaking stance.
- Then modulate confidence and hedging based on topic fit:
  - if the topic strongly matches the persona's work, study, hobbies, or lived experience, confidence may rise and hedging may drop somewhat
  - if the topic is far from the persona's profile, confidence should drop and hedging should rise
- Keep these shifts believable and proportional rather than dramatic.
""".strip()


def build_stylometry_generation_user_prompt(
    *,
    persona_biography: str,
    persona_details: dict,
    persona_country: str,
) -> str:
    """Build the prompt used to create a cached stylometric profile."""
    normalized_details = json.dumps(
        {
            "country": persona_country,
            "age_group": persona_details.get("age_group"),
            "gender": persona_details.get("gender"),
            "education": persona_details.get("education"),
            "municipality": persona_details.get("municipality"),
            "vote_2030": persona_details.get("vote_2030"),
        },
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )

    return (
        "Infer a reusable linguistic profile for this persona.\n\n"
        "Persona details:\n"
        f"{normalized_details}\n\n"
        "Persona biography:\n"
        f"{persona_biography}\n\n"
        "Output constraints:\n"
        '- "register": plain | everyday | polished | articulate\n'
        '- "sentence_style": short | mixed | long\n'
        '- "abstraction_level": concrete | mixed | abstract\n'
        '- "vocabulary_level": simple | moderate | advanced\n'
        '- "hedging_style": low | medium | high\n'
        '- "confidence_style": tentative | balanced | assured\n'
        '- "warmth_style": reserved | warm | expressive\n'
        '- "explanation_style": example_first | balanced | concept_first\n'
        '- "reasoning_style": practical | reflective | analytical | blended\n'
        '- "profile_summary": 2-4 sentences\n'
        '- "evidence": short array of direct evidence phrases from the biography\n'
    )


def build_stylometry_judge_prompt(*, stylometric_profile: dict) -> str:
    """Build the stylometry prompt segment passed into the judge bundle."""
    return (
        f"{STYLOMETRY_JUDGE_SUBPROMPT}\n\n"
        "Stylometric profile context:\n"
        f"{json.dumps(stylometric_profile, ensure_ascii=False, indent=2)}"
    )
