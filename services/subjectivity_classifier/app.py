"""HTTP wrapper for fractalego/subjectivity_classifier."""

import logging
import os

from flask import Flask, jsonify, request
from nltk.tokenize import sent_tokenize

from subjectivity.subjectivity_classifier import SubjectivityClassifier
from subjectivity.utils import convert_text_into_vector_sequence


MODEL_PATH = "/opt/subjectivity_classifier/data/save/subj-29.tf"
DEFAULT_WORD_PATH = "/opt/subjectivity_classifier/data/word_embeddings/glove.6B.50d.txt"

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("subjectivity_classifier_service")

WORD_PATH = os.getenv("SUBJECTIVITY_WORD_EMBEDDINGS_PATH", DEFAULT_WORD_PATH)
if not os.path.isfile(WORD_PATH):
    log.warning(
        "Configured embeddings file %s was not found; falling back to bundled development embeddings.",
        WORD_PATH,
    )
    WORD_PATH = DEFAULT_WORD_PATH

if WORD_PATH == DEFAULT_WORD_PATH:
    log.warning(
        "Using bundled development embeddings. Mount the full GloVe 6B 50d file and set "
        "SUBJECTIVITY_WORD_EMBEDDINGS_PATH for higher-fidelity scoring."
    )
else:
    log.info("Using external word embeddings from %s.", WORD_PATH)

log.info("Loading fractalego/subjectivity_classifier model.")
classifier = SubjectivityClassifier(model_filename=MODEL_PATH, word_filename=WORD_PATH)
log.info("Subjectivity classifier model loaded.")


def _sanitize_text(text):
    """Mirror the package sanitizer so probabilities match hard classification."""
    text = text.replace("\n", ".\n")
    text = text.replace(".[", ". [")
    text = text.replace(".[", ". [")
    text = text.replace("...", ".")
    text = text.replace("..", ".")
    text = text.replace("\n.", "\n")
    return text


def _clean_sentence(text):
    """Mirror the package sentence cleaner."""
    text = text.replace("\n", "")
    if text == ".":
        return ""
    return text


def _sentence_probabilities(sentence):
    """Return softmax probabilities from the legacy model before hard labeling."""
    vectors = convert_text_into_vector_sequence(classifier._word_model, sentence)
    output = classifier._subj_model._SubjectivityPredictor__predict([vectors])[0]
    subjective_probability = float(output[0])
    objective_probability = float(output[1])
    label = "subjective" if subjective_probability > objective_probability else "objective"
    return {
        "sentence": sentence,
        "label": label,
        "subjective_probability": round(subjective_probability, 6),
        "objective_probability": round(objective_probability, 6),
    }


def _score_text(text):
    """Score every sentence with soft probabilities and hard labels."""
    scored_sentences = []
    for sentence in sent_tokenize(_sanitize_text(text)):
        sentence = _clean_sentence(sentence)
        if not sentence:
            continue
        scored_sentences.append(_sentence_probabilities(sentence))

    objective = [
        item["sentence"]
        for item in scored_sentences
        if item["label"] == "objective"
    ]
    subjective = [
        item["sentence"]
        for item in scored_sentences
        if item["label"] == "subjective"
    ]
    count = len(scored_sentences)
    if count:
        subjectivity_score = sum(
            item["subjective_probability"] for item in scored_sentences
        ) / count
        objectivity_score = sum(
            item["objective_probability"] for item in scored_sentences
        ) / count
    else:
        subjectivity_score = 0.0
        objectivity_score = 0.0

    return {
        "objective": objective,
        "subjective": subjective,
        "sentences": scored_sentences,
        "subjectivity_score": round(subjectivity_score, 6),
        "objectivity_score": round(objectivity_score, 6),
    }


@app.route("/health", methods=["GET"])
def health():
    """Report whether the classifier process is alive."""
    log.info("Health check received.")
    return jsonify(
        {
            "status": "ok",
            "model": "fractalego/subjectivity_classifier",
            "scoring": "softmax_probabilities",
            "word_embeddings": WORD_PATH,
        }
    )


@app.route("/classify", methods=["POST"])
def classify():
    """Classify text into objective and subjective sentence lists."""
    payload = request.get_json(silent=True) or {}
    text = payload.get("text", "")
    if not isinstance(text, str) or not text.strip():
        log.info("Classification request received with empty text.")
        return jsonify({"objective": [], "subjective": []})

    result = _score_text(text)
    log.info(
        "Scored text into %s objective and %s subjective sentence(s): %.3f objective probability, %.3f subjective probability.",
        len(result.get("objective", [])),
        len(result.get("subjective", [])),
        result.get("objectivity_score", 0.0),
        result.get("subjectivity_score", 0.0),
    )
    return jsonify(
        {
            "objective": result.get("objective", []),
            "subjective": result.get("subjective", []),
            "sentences": result.get("sentences", []),
            "subjectivity_score": result.get("subjectivity_score", 0.0),
            "objectivity_score": result.get("objectivity_score", 0.0),
            "scoring": "softmax_probabilities",
        }
    )
