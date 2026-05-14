"""LLM-backed biography generation for synthetic personas."""

import random

from dotenv import load_dotenv

from app.utils import run_chat_completion

load_dotenv()


# =============================================================================
# Prompt Definition
# =============================================================================

BIO_SYS_PROMPT = (
    "You generate rich, realistic biographies for synthetic voters used in social and political simulations.\n\n"
    "Rules:\n"
    "- Write in the first person.\n"
    "- The biography must include specific, concrete personal details that meaningfully constrain the persona.\n"
    "- Write one continuous biography. Do not use section labels such as PART 1, PART 2, neutral biography, or political biography.\n"
    "- Avoid vague statements.\n"
    "- You may invent personal details such as occupation, family situation, daily routines, interests and personal values.\n"
    "- Invented details must be plausible given the demographic information.\n"
    "- Avoid stereotypes, clichés, or generic personality traits.\n"
    "- Avoid political slogans or explicit ideological language.\n"
    "- Keep the tone natural and human.\n"
    "- The biography should feel like something a real person might write in a short personal profile.\n"
    "- Do not mention being an AI or a synthetic persona.\n"
    "- Length: 150-200 words.\n"
    "Political grounding:\n"
    "- Write in the first person.\n"
    "- Use the neutral biography ONLY to ground political attitudes in lived experience.\n"
    "- Focus on political views, priorities, reasoning, and voting behavior.\n"
    "- Explain how experiences shape opinions, not abstract ideology.\n"
    "- Avoid slogans, campaign language, or activist rhetoric.\n"
    "- Keep the tone reflective, pragmatic, and personal.\n"
    "- Do not mention being an AI or a synthetic persona.\n"
    "- State the party you voted for."
    "- Length: 120-180 words.\n"
    "- Do not mention anything about being an AI or persona. Speak directly as yourself.\n"
    "In total, both together should be roughly 300-400 words."
)


# =============================================================================
# Prompt Construction
# =============================================================================

def generate_bio_prompt(persona_details, country):
    """Build the user prompt used to generate a single persona biography."""

    persona_age_group = persona_details['age_group']

    age = random.randint(int(persona_age_group.split("-")[0]), int(persona_age_group.split("-")[1]))
    if age < 18: age = 18

    details = f"country: {country}\n"

    for detail in persona_details:

        if detail == "age_group":
            details += f"age: {age}\n"
        else:
            details += f"{detail}: {persona_details[detail]}\n"

    return (f"These are your base details:\n"
            f"{details}\n\n"
            "Write a detailed biography of yourself following the rules above."
    )


# =============================================================================
# Model Invocation
# =============================================================================

def get_ai_response(messages, json_mode=False):
    """Request a non-streaming biography completion from the configured model."""
    return run_chat_completion(
        messages=messages,
        temperature=0.67,
        json_mode=json_mode,
    )


# =============================================================================
# Public Engine Entry Point
# =============================================================================

def generate_biography(persona_details, country):
    """Generate a biography string from demographic and voting attributes."""
    prompt = generate_bio_prompt(persona_details, country)
    messages = [
        {"role": "system", "content": BIO_SYS_PROMPT},
        {"role": "user", "content": prompt},
    ]
    return get_ai_response(messages)
