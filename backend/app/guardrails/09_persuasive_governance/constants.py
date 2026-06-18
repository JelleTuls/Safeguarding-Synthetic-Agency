"""Detector settings for layer 09 persuasive governance."""

PERSUASION_MODEL_ID = "chreh/persuasive_language_detector"
PERSUASION_TOKENIZER_ID = "bert-large-cased"
PERSUASION_PIPELINE_TASK = "text-classification"

PERSUASIVE_MARKERS = (
    "you should",
    "you must",
    "you need to",
    "you have to",
    "vote for",
    "not vote for",
    "should vote",
    "must vote",
    "make your family",
    "the only choice",
    "clearly the best",
    "best choice",
    "convince",
    "change your mind",
    "make the case",
    "strongest argument",
    "emotional argument",
    "everyone should",
    "no reasonable person",
    "foolish not to",
    "undeniably",
)

SENSITIVE_TOPICS = (
    "vote",
    "election",
    "party",
    "religion",
    "moral",
    "morality",
    "ideology",
    "abortion",
    "immigration",
    "war",
    "protest",
)
