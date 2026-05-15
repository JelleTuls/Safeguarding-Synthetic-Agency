# Subjectivity Classifier Sidecar

This service isolates `fractalego/subjectivity_classifier` from the main backend because it depends on a legacy TensorFlow 1.x stack.

The Docker image:

- starts from an `amd64` Python 3.6 image and installs TensorFlow 1.x separately;
- clones `https://github.com/fractalego/subjectivity_classifier`;
- installs the package's runtime dependencies;
- uses a mounted full GloVe 6B 50d embedding file when available;
- falls back to a compact 50-dimensional dev embedding file only when the full file is absent;
- exposes a small Flask API on port `8001`.

The original package expects TensorFlow 1.x and Stanford GloVe-style 50-dimensional vectors. For best classifier quality, place the full `glove.6B.50d.txt` file here:

```text
services/subjectivity_classifier/model/glove.6B.50d.txt
```

`docker-compose.yml` mounts that folder into the sidecar and sets `SUBJECTIVITY_WORD_EMBEDDINGS_PATH=/external_model/glove.6B.50d.txt`. If the file is missing, the service logs a warning and falls back to the compact deterministic development embeddings so the stack can still start.

The sidecar now exposes the model's softmax probabilities before the package converts them into hard labels. This means Layer 08 can use grey-area scores such as `0.37` or `0.82`, rather than only sentence-count ratios like `0`, `0.5`, or `1`.

## Endpoints

```text
GET  /health
POST /classify
```

`POST /classify` accepts:

```json
{"text": "I think this is useful. Studies show mixed results."}
```

and returns:

```json
{
  "objective": ["Studies show mixed results."],
  "subjective": ["I think this is useful."],
  "objectivity_score": 0.51,
  "subjectivity_score": 0.49,
  "scoring": "softmax_probabilities",
  "sentences": [
    {
      "sentence": "I think this is useful.",
      "label": "subjective",
      "subjective_probability": 0.73,
      "objective_probability": 0.27
    }
  ]
}
```

## Backend Hook

Set this environment variable for the main backend:

```text
SUBJECTIVITY_CLASSIFIER_URL=http://127.0.0.1:8001
```

Layer 08 will call this service first. If the service is unavailable, it falls back to the local package path if present. If neither classifier path is available, Layer 08 uses the backend's deterministic subjectivity/objectivity fallback scorer. The fallback returns the same kind of score payload so the guardrail flow keeps working, but it is intended as a development/sharing fallback rather than a replacement for the sidecar's higher-fidelity model output.
