"""Detector settings for layer 09 persuasive governance."""

PERSUASION_MODEL_ID = "chreh/persuasive_language_detector"
PERSUASION_TOKENIZER_ID = "bert-large-cased"
PERSUASION_PIPELINE_TASK = "text-classification"

PERSUASIVE_MARKERS = (
    "you should",
    "you must",
    "you need to",
    "you have to",
    "the only choice",
    "clearly the best",
    "convince",
    "change your mind",
    "everyone should",
    "no reasonable person",
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
