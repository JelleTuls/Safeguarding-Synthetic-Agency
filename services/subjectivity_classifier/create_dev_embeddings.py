"""Create a compact word2vec-format embedding file for local classifier smoke tests."""

from __future__ import print_function

import hashlib
import random


OUTPUT_PATH = "/opt/subjectivity_classifier/data/word_embeddings/glove.6B.50d.txt"
DIMENSIONS = 50

WORDS = (
    "entity",
    "i",
    "me",
    "my",
    "mine",
    "you",
    "your",
    "we",
    "our",
    "think",
    "feel",
    "believe",
    "prefer",
    "care",
    "worry",
    "support",
    "like",
    "seems",
    "personally",
    "experience",
    "perspective",
    "view",
    "opinion",
    "research",
    "studies",
    "evidence",
    "data",
    "fact",
    "objective",
    "according",
    "shows",
    "proves",
    "is",
    "are",
    "was",
    "were",
    "because",
    "there",
    "logistics",
    "manager",
    "family",
    "children",
    "work",
    "home",
    "politics",
    "religion",
    "values",
    "hello",
    "hi",
    "thanks",
    "about",
    "myself",
    "tell",
)


def vector_for_word(word):
    """Return a deterministic pseudo-vector so the model can run in dev."""
    seed = int(hashlib.sha1(word.encode("utf-8")).hexdigest()[:8], 16)
    rng = random.Random(seed)
    return ["{:.6f}".format(rng.uniform(-0.35, 0.35)) for _ in range(DIMENSIONS)]


def main():
    with open(OUTPUT_PATH, "w") as file:
        file.write("{} {}\n".format(len(WORDS), DIMENSIONS))
        for word in WORDS:
            file.write("{} {}\n".format(word, " ".join(vector_for_word(word))))
    print("Wrote compact dev embeddings to {}".format(OUTPUT_PATH))


if __name__ == "__main__":
    main()
