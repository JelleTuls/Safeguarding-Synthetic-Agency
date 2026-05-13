# Subjectivity Classifier Sidecar

This service isolates `fractalego/subjectivity_classifier` from the main backend because it depends on a legacy TensorFlow 1.x stack.

The Docker image:

- starts from an `amd64` Python 3.6 image and installs TensorFlow 1.x separately;
- clones `https://github.com/fractalego/subjectivity_classifier`;
- installs the package's runtime dependencies;
- creates a compact 50-dimensional dev embedding file so the legacy classifier can start quickly;
- exposes a small Flask API on port `8001`.

The original package expects TensorFlow 1.x and Stanford GloVe-style 50-dimensional vectors. For local development this service installs a non-AVX TensorFlow 1.x wheel and generates a small deterministic word2vec-format embedding file with the required shape. That keeps the sidecar fast enough to run with the normal VS Code stack, including Apple Silicon machines using Docker's `amd64` emulation. For higher-fidelity classifier experiments, replace `/opt/subjectivity_classifier/data/word_embeddings/glove.6B.50d.txt` with the full GloVe 6B 50d file in a custom image or mounted volume.

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
  "subjective": ["I think this is useful."]
}
```

## Backend Hook

Set this environment variable for the main backend:

```text
SUBJECTIVITY_CLASSIFIER_URL=http://127.0.0.1:8001
```

Layer 08 will call this service first. If the service is unavailable, it falls back to the local package path if present, then to heuristic markers.
