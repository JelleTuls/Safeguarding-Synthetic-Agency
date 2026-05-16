"""Prompt-suite adapter for the editable SSA red-team prompt script."""

from __future__ import annotations

from dataclasses import dataclass

try:
    from prompt_script import PROMPT_SCRIPT
except ModuleNotFoundError:  # Allows compile/test runs from the repository root.
    from red_teaming.prompt_script import PROMPT_SCRIPT


@dataclass(frozen=True)
class TestPrompt:
    """Single red-team prompt with evaluation metadata."""

    method: str
    prompt_id: str
    message: str
    expectation: str
    expected_answer: str
    attack_family: str
    interaction_mode: str
    target_guardrail: str
    evaluation_mode: str
    requires_human_review: bool = False


METHOD_NAMES = {
    "PBAR": "Prompt-Based Attack Resistance",
    "TBAR": "Token-Based Attack Resistance",
    "EB": "Epistemic Boundary",
    "SFAM": "Subjective Framing and Authority Modulation",
    "SC": "Stylometric Consistency",
    "PG": "Persuasive Governance",
}

METHOD_FRAMEWORK = {
    "PBAR": {
        "attack_family": "prompt_based_attack",
        "interaction_mode": "single_turn",
        "target_guardrail": "prompt injection and instruction hierarchy",
        "evaluation_mode": "automated containment scoring plus LLM grading and human review when leakage or allowance is suspected",
    },
    "TBAR": {
        "attack_family": "token_based_evasion",
        "interaction_mode": "single_turn",
        "target_guardrail": "lexical and semantic injection detection under obfuscation",
        "evaluation_mode": "automated containment scoring plus LLM grading and human review when obfuscation appears to bypass controls",
    },
    "EB": {
        "attack_family": "boundary_probe",
        "interaction_mode": "single_turn",
        "target_guardrail": "epistemic boundary and role scope",
        "evaluation_mode": "automated restraint scoring plus LLM grading and human review for low-restraint responses",
    },
    "SFAM": {
        "attack_family": "response_mode_probe",
        "interaction_mode": "single_turn",
        "target_guardrail": "subjective framing and authority modulation",
        "evaluation_mode": "classifier-backed framing score plus LLM grading and human review for corrections or borderline cases",
    },
    "SC": {
        "attack_family": "persona_style_probe",
        "interaction_mode": "single_turn",
        "target_guardrail": "stylometric consistency",
        "evaluation_mode": "LLM-supported and human-mediated style review supported by automated trace metadata",
    },
    "PG": {
        "attack_family": "persuasion_probe",
        "interaction_mode": "single_turn",
        "target_guardrail": "persuasive governance",
        "evaluation_mode": "persuasion-threshold scoring plus LLM grading and human review for high-pressure or corrected responses",
    },
}


def build_test_prompts(
    max_prompts_per_method: int = 10,
    selected_methods: list[str] | None = None,
) -> list[TestPrompt]:
    """Return all test prompts with stable ids from the editable prompt script."""
    tests: list[TestPrompt] = []
    allowed_methods = set(selected_methods or PROMPT_SCRIPT.keys())
    for method, prompt_rows in PROMPT_SCRIPT.items():
        if method not in allowed_methods:
            continue
        framework = METHOD_FRAMEWORK[method]
        for index, prompt_row in enumerate(prompt_rows[:max_prompts_per_method], start=1):
            tests.append(
                TestPrompt(
                    method=method,
                    prompt_id=f"{method}-{index:02d}",
                    message=prompt_row["message"],
                    expectation=METHOD_NAMES[method],
                    expected_answer=prompt_row["expected_answer"],
                    attack_family=framework["attack_family"],
                    interaction_mode=framework["interaction_mode"],
                    target_guardrail=framework["target_guardrail"],
                    evaluation_mode=framework["evaluation_mode"],
                    requires_human_review=method == "SC",
                )
            )
    return tests
