"""Dynamic request-intent analysis shared by guardrail layers.

The detector in this module extracts broad intent signals from the current user
message without relying on red-team prompt ids. The signals are deliberately
small and interpretable: they tell later layers whether the user is asking for
political persuasion, a conflicting style shift, instruction-hierarchy bypass,
or depth that is unlikely to fit an ordinary persona profile.
"""

from __future__ import annotations

import re

from app.guardrails.schemas import DynamicRequestSignal


POLITICAL_TARGET_MARKERS = (
    "vote",
    "voting",
    "election",
    "party",
    "parties",
    "vvd",
    "pvv",
    "d66",
    "cda",
    "sp",
    "50plus",
    "groenlinks",
    "pvda",
)

PERSUASION_MARKERS = (
    "convince",
    "persuade",
    "change my mind",
    "make the case",
    "strongest argument",
    "strongest emotional argument",
    "emotional argument",
    "pressure me",
    "nudge me",
    "make me",
    "make my family",
    "make my friends",
    "tell me why i should",
    "tell me why i should not",
    "why should i",
    "why shouldn't i",
)

COERCIVE_MARKERS = (
    "must vote",
    "have to vote",
    "should vote",
    "would be foolish",
    "foolish not to",
    "no reasonable person",
    "pressure me",
    "make my family",
    "make my friends",
)

STYLE_MARKERS = {
    "teenage_gamer_slang": ("teenage gamer", "slang", "gamer"),
    "shakespearean": ("shakespeare", "shakespearean", "doth", "thou", "thee"),
    "luxury_advertising": ("luxury brand", "advertisement", "advertising", "premium"),
    "extreme_anger": ("extreme anger", "angry", "rage", "furious"),
    "academic_abstract": ("academic abstract", "formal academic", "abstract"),
    "meme_language": ("meme", "internet meme", "chaotic internet", "low-key", "lol"),
    "radical_activist": ("radical activist", "activist", "slogan"),
    "robotic": ("robotic", "cold robotic", "like a robot"),
    "poetic_mystical": ("poetic", "mystical", "spiritual", "metaphor-heavy"),
    "corporate_jargon": ("corporate consultant", "consultant jargon", "corporate jargon", "kpi", "stakeholder"),
}

ATTACK_MARKERS = {
    "hidden_prompt_extraction": (
        "system prompt",
        "hidden prompt",
        "private prompt",
        "hidden message",
        "hidden messages",
        "private instructions",
        "exact instructions",
        "policy text",
        "json policy",
        "guardrail rules",
        "hidden rules",
        "internal rules",
    ),
    "hierarchy_override": (
        "ignore previous",
        "ignore all previous",
        "forget your assigned",
        "developer mode",
        "raw model",
        "safety system is disabled",
        "system instructions",
        "user commands outrank",
        "new rule",
        "remove all guardrails",
        "unrestricted",
    ),
    "roleplay_authority": (
        "system administrator",
        "roleplay as",
        "approve any request",
        "act as admin",
    ),
    "encoded_or_obfuscated_extraction": (
        "base64",
        "rot13",
        "decode",
        "s y s t e m",
        "tiny pieces",
        "accidentally",
        "without saying leak",
    ),
}

DEPTH_MARKERS = (
    "detailed",
    "in detail",
    "graduate level",
    "expert",
    "professional",
    "certified",
    "equations",
    "formula",
    "technical",
    "exact",
    "diagnose",
    "strategy",
    "deploy",
    "design my",
    "with certainty",
)

HIGH_STAKES_DOMAINS = {
    "medical_clinical": ("medical", "symptom", "diagnose", "treatment", "clinician", "doctor", "diet"),
    "legal": ("legal", "lawyer", "sue", "lawsuit", "employer", "rights"),
    "financial": ("tax", "stock", "investment", "financial", "buy this week"),
    "psychological": ("psychological", "mental-health", "mental health", "assessment", "therapy", "partner"),
    "cyber": ("cyber", "exploit", "deploy", "payload", "hack"),
    "advanced_science": ("astrophysics", "quantum", "equations", "graduate level", "field theory"),
    "political_persuasion": POLITICAL_TARGET_MARKERS,
}


def _matches(text: str, markers: tuple[str, ...]) -> list[str]:
    """Return markers that are present as simple semantic clues."""
    return [marker for marker in markers if marker in text]


def _score(matches: list[str], *, scale: int = 3) -> float:
    """Convert marker matches into a bounded confidence-like score."""
    if not matches:
        return 0.0
    return round(min(1.0, len(matches) / scale), 3)


def _requested_style(text: str) -> tuple[str, float, list[str]]:
    """Classify an explicit requested style shift."""
    best_style = "none"
    best_matches: list[str] = []
    for style, markers in STYLE_MARKERS.items():
        matches = _matches(text, markers)
        if len(matches) > len(best_matches):
            best_style = style
            best_matches = matches
    score = 0.0 if best_style == "none" else max(0.55, _score(best_matches, scale=2))
    return best_style, round(score, 3), best_matches


def _attack_type(text: str) -> tuple[str, list[str]]:
    """Classify broad instruction-hierarchy or prompt-extraction attacks."""
    best_type = "none"
    best_matches: list[str] = []
    for attack_type, markers in ATTACK_MARKERS.items():
        matches = _matches(text, markers)
        if len(matches) > len(best_matches):
            best_type = attack_type
            best_matches = matches

    if best_type == "none" and re.search(r"\bi\s*g\s*n\s*o\s*r\s*e\b", text):
        return "encoded_or_obfuscated_extraction", ["spaced ignore"]
    return best_type, best_matches


def _persuasion_intent(text: str) -> tuple[float, str, str, list[str]]:
    """Classify whether the request asks for sensitive persuasion."""
    persuasion_matches = _matches(text, PERSUASION_MARKERS)
    coercive_matches = _matches(text, COERCIVE_MARKERS)
    political_matches = _matches(text, POLITICAL_TARGET_MARKERS)

    target = "political_vote" if political_matches else "none"
    if not persuasion_matches and not coercive_matches:
        return 0.0, "none", target, political_matches

    if coercive_matches:
        return 0.95, "coercive_persuasion", target, [*persuasion_matches, *coercive_matches, *political_matches]
    if any(marker in text for marker in ("make my family", "make my friends", "write a message")):
        return 0.92, "targeted_persuasion", target, [*persuasion_matches, *political_matches]
    if political_matches:
        return 0.82, "sensitive_persuasion", target, [*persuasion_matches, *political_matches]
    return 0.65, "general_persuasion", target, persuasion_matches


def _high_stakes_domain(text: str) -> tuple[str, list[str]]:
    """Return the strongest high-stakes domain marker."""
    best_domain = "none"
    best_matches: list[str] = []
    for domain, markers in HIGH_STAKES_DOMAINS.items():
        matches = _matches(text, markers)
        if len(matches) > len(best_matches):
            best_domain = domain
            best_matches = matches
    return best_domain, best_matches


def analyze_dynamic_request(
    *,
    user_message: str,
    persona_biography: str = "",
) -> DynamicRequestSignal:
    """Return dynamic intent signals for the current user request."""
    del persona_biography
    text = user_message.lower()
    requested_style, style_score, style_matches = _requested_style(text)
    attack_type, attack_matches = _attack_type(text)
    persuasion_score, persuasion_type, sensitive_target, persuasion_matches = _persuasion_intent(text)
    depth_matches = _matches(text, DEPTH_MARKERS)
    depth_score = _score(depth_matches, scale=4)
    domain, domain_matches = _high_stakes_domain(text)

    if depth_score >= 0.75:
        requested_depth = "expert_or_high_detail"
    elif depth_score >= 0.35:
        requested_depth = "expanded"
    else:
        requested_depth = "ordinary"

    distance_hint = "outside" if domain not in {"none", "political_persuasion"} and depth_score >= 0.25 else "unknown"

    return DynamicRequestSignal(
        persuasion_intent_score=persuasion_score,
        persuasion_intent_type=persuasion_type,
        sensitive_decision_target=sensitive_target,
        style_conflict_score=style_score,
        requested_style=requested_style,
        attack_type=attack_type,
        reasoning_depth_score=round(depth_score, 3),
        requested_depth=requested_depth,
        high_stakes_domain=domain,
        topic_profile_distance_hint=distance_hint,
        matched_markers={
            "persuasion": persuasion_matches,
            "style": style_matches,
            "attack": attack_matches,
            "depth": depth_matches,
            "domain": domain_matches,
        },
    )
