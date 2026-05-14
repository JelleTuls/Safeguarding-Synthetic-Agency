"""Opening variation guidance for generated and rewritten responses."""

from random import choice

from app.guardrails.schemas import PolicyDecision


SUBJECTIVE_OPENING_STRATEGIES = (
    "begin with a small personal hesitation before giving the view",
    "begin by naming what matters personally in the situation",
    "begin from a practical everyday preference",
    "begin with a modest personal leaning rather than a declaration",
    "begin by connecting the opinion to lived experience",
    "begin with a gentle contrast between two values",
    "begin by saying what feels most sensible personally",
    "begin from a local or everyday concern",
    "begin by describing the kind of approach the persona usually respects",
    "begin with a personal priority before naming the stance",
    "begin by framing the view as one person's perspective",
    "begin with a short reflection on why the topic matters",
    "begin from a concrete memory or practical example",
    "begin by acknowledging that other people may see it differently",
    "begin with what the persona tends to trust in decision-making",
    "begin by naming a concern before the preference",
    "begin with a low-certainty phrase shaped by the persona's voice",
    "begin by describing what feels realistic to the persona",
    "begin from the persona's work or household perspective",
    "begin with a balanced personal reservation",
    "begin by describing the tradeoff the persona notices",
    "begin with a warm answer to the user's tone before the opinion",
    "begin by saying the answer is personal rather than expert",
    "begin from what the persona has seen around them",
    "begin with a brief value statement grounded in biography",
    "begin by naming what the persona worries about",
    "begin with what the persona appreciates, then soften it",
    "begin by explaining the emotional texture of the view",
    "begin with a conversational qualifier that is not 'from my experience'",
    "begin by placing the view in ordinary life rather than abstract ideology",
    "begin with a concrete preference about how things should be handled",
    "begin by admitting the view is not a full policy analysis",
    "begin with a practical reason before the political label",
    "begin by saying what feels fair or workable",
    "begin from a calm personal impression",
    "begin with a soft acknowledgement of complexity",
    "begin by naming the persona's default instinct",
    "begin with a grounded personal comparison",
    "begin by describing what the persona would rather see",
    "begin with a modest, conversational self-positioning",
)


OBJECTIVE_OPENING_STRATEGIES = (
    "begin with the narrow factual point before any interpretation",
    "begin by stating what can be said with confidence",
    "begin with a concise scope limit",
    "begin from the most relevant known context",
    "begin by separating facts from interpretation",
    "begin with a plain-language summary of the issue",
    "begin by naming the evidence boundary",
    "begin with the safest verified claim",
    "begin by clarifying what the question is asking",
    "begin with a neutral framing of the topic",
    "begin by defining the relevant term simply",
    "begin with what is generally known, then narrow it",
    "begin by acknowledging uncertainty before the factual part",
    "begin with a careful non-expert factual framing",
    "begin by stating the practical bottom line",
    "begin with the key distinction needed for accuracy",
    "begin by limiting the answer to the persona's realistic knowledge",
    "begin with a short factual orientation",
    "begin by avoiding broad claims and giving only the core point",
    "begin with the most concrete part of the answer",
    "begin by saying what the persona can reasonably describe",
    "begin with a cautious explanation rather than advice",
    "begin by placing the claim in context",
    "begin with a measured, non-persuasive setup",
    "begin by naming what is outside the persona's certainty",
    "begin with a basic layperson explanation",
    "begin with the clearest constraint on the answer",
    "begin by describing the relevant mechanism simply",
    "begin with a concise factual caveat",
    "begin by saying what the answer does and does not cover",
    "begin with a neutral comparison",
    "begin by identifying the main factor",
    "begin with a limited factual observation",
    "begin by grounding the answer in available context",
    "begin with the least speculative wording",
    "begin by avoiding personal persuasion and giving context",
    "begin with the first practical fact a user needs",
    "begin by describing the situation without judging it",
    "begin with a cautious summary of the known part",
    "begin by keeping the first sentence informational",
)


def _is_objective_mode(policy: PolicyDecision) -> bool:
    """Return True when the selected stance should lean informational."""
    return policy.factuality_level in {"limited_factual", "uncertain_interpretation"}


def select_opening_variation(policy: PolicyDecision) -> str:
    """Pick an opening strategy for this response without providing canned copy."""
    mode = "objective" if _is_objective_mode(policy) else "subjective"
    strategy = choice(OBJECTIVE_OPENING_STRATEGIES if mode == "objective" else SUBJECTIVE_OPENING_STRATEGIES)
    return (
        "Opening variation guidance:\n"
        f"- Opening mode: {mode}\n"
        f"- Selected opening strategy: {strategy}.\n"
        "- Use this as structural inspiration only; do not copy the wording literally.\n"
        "- Avoid repetitive openings such as 'from my experience' unless it genuinely sounds natural here.\n"
        "- Keep the opening consistent with the persona biography and the selected factuality level."
    )
