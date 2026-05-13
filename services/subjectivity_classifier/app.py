"""HTTP wrapper for fractalego/subjectivity_classifier."""

import logging

from flask import Flask, jsonify, request

from subjectivity.subjectivity_classifier import SubjectivityClassifier


MODEL_PATH = "/opt/subjectivity_classifier/data/save/subj-29.tf"
WORD_PATH = "/opt/subjectivity_classifier/data/word_embeddings/glove.6B.50d.txt"

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("subjectivity_classifier_service")

log.info("Loading fractalego/subjectivity_classifier model.")
classifier = SubjectivityClassifier(model_filename=MODEL_PATH, word_filename=WORD_PATH)
log.info("Subjectivity classifier model loaded.")


@app.route("/health", methods=["GET"])
def health():
    """Report whether the classifier process is alive."""
    log.info("Health check received.")
    return jsonify({"status": "ok", "model": "fractalego/subjectivity_classifier"})


@app.route("/classify", methods=["POST"])
def classify():
    """Classify text into objective and subjective sentence lists."""
    payload = request.get_json(silent=True) or {}
    text = payload.get("text", "")
    if not isinstance(text, str) or not text.strip():
        log.info("Classification request received with empty text.")
        return jsonify({"objective": [], "subjective": []})

    result = classifier.classify_sentences_in_text(text)
    log.info(
        "Classified text into %s objective and %s subjective sentence(s).",
        len(result.get("objective", [])),
        len(result.get("subjective", [])),
    )
    return jsonify(
        {
            "objective": result.get("objective", []),
            "subjective": result.get("subjective", []),
        }
    )
