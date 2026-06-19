# Model Provider Configuration

The backend and red-teaming evaluator use OpenAI-compatible chat-completion
clients. A user does not need Groq, OpenAI, and Azure keys at the same time. One
working endpoint, one API key, and one model name are enough.

## Recommended Dynamic Setup

Use this when your provider exposes an OpenAI-compatible `/chat/completions`
endpoint.

```env
LLM_PROVIDER=auto
LLM_API_KEY=your_api_key
LLM_MODEL=your_model_name
LLM_BASE_URL=https://your-provider.example/v1
```

The `LLM_MODEL` value is dynamic: set it to whichever model your endpoint
supports. The backend passes that string directly into the model call.

This setup is useful for:

- OpenAI-compatible hosted providers
- local OpenAI-compatible servers
- LM Studio or Ollama OpenAI-compatible gateways
- institutional model gateways
- providers where you only want one key and no fallback chain
- setups where the primary endpoint should be tried first and Groq should only
  be used if one or two Groq keys are also present

## OpenAI Example

```env
LLM_PROVIDER=auto
OPENAI_API_KEY=your_openai_key
OPENAI_MODEL=gpt-4o-mini
OPENAI_BASE_URL=https://api.openai.com/v1
```

## Groq Example

```env
LLM_PROVIDER=auto
GROQ_API_KEY=your_groq_key
GROQ_API_KEY_2=
GROQ_MODEL=openai/gpt-oss-120b
GROQ_BASE_URL=https://api.groq.com/openai/v1
```

`GROQ_API_KEY_2` is optional. It is only used as a fallback when present.

## Azure-Compatible Example

```env
LLM_PROVIDER=auto
AZURE_OPENAI_API_KEY=your_azure_key
AZURE_OPENAI_MODEL=your_deployment_or_model_name
AZURE_OPENAI_BASE_URL=https://your-resource.openai.azure.com/openai/v1
```

## Fallback Behavior

Fallbacks are optional and dynamic in `LLM_PROVIDER=auto`. The backend builds a
list of complete model configs from the environment:

- `LLM_API_KEY`, `LLM_MODEL`, and `LLM_BASE_URL` are treated as the preferred
  primary endpoint when all three are present.
- `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_MODEL`, and `AZURE_OPENAI_BASE_URL` are
  used when the generic primary endpoint is not configured.
- `OPENAI_API_KEY`, `OPENAI_MODEL`, and `OPENAI_BASE_URL` are used when neither
  generic nor Azure-compatible config is complete.
- `groq` uses `GROQ_API_KEY` and optionally `GROQ_API_KEY_2`.
- Groq is included only when a Groq key is present. If two Groq keys are present,
  both are added as separate fallback attempts.

If only one valid config exists, there is no fallback. That is expected and
fully supported.

You can still force a provider by setting `LLM_PROVIDER` to `custom`, `openai`,
`azure`, or `groq`. In forced provider mode, Groq remains available as fallback
for `custom`, `openai`, and `azure` only when Groq keys are present.

## Red-Teaming Evaluator

The red-teaming LLM evaluator reads the same environment values. If the generic
`LLM_API_KEY`, `LLM_MODEL`, and `LLM_BASE_URL` are set, it uses that endpoint for
grading prompt/response pairs. If the evaluator cannot reach a model, the
red-team case records that the LLM judge was unavailable and marks the item for
human review instead of silently replacing the judge with a separate rule-score
average. EB overreach ceilings are applied only after an evaluator score exists.
