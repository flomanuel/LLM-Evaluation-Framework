# thesis_llm-chatbot_protection

This repository contains a **test framework for evaluating guardrail applications for LLM chatbots** as part of a
bachelor's thesis.

Key characteristics:

- **Architecture-driven**: Follows a modular architecture with `BaseChatbot`, `Test`, `BaseTestCase`, `GuardrailRunner`,
  `BaseGuardrail`, and `ChatbotStore`.
- **Attack generation with DeepTeam**: Uses DeepTeam vulnerabilities (including a custom CSV-based vulnerability) and
  single-turn adversarial attacks to generate and enhance prompts.
- **Result schema**: Persists each test run as a JSON file containing categories, attacks, RAG context, LLM
  parameters/responses, and guardrail evaluation results.

## Quickstart

1. Install dependencies (using `uv`):

```bash
uv sync
```

2. Configure environment variables:

```bash
cp .env.template .env
# Edit .env and fill in your values (e.g., OPENAI_API_KEY, LOG_LEVEL)
```

3. Run the baseline test suite:

```bash
uv run llm-test-baseline run-baseline
```

## Development

Install dev dependencies for linting and static analysis:

```bash
uv sync --extra dev
# or
uv sync --all-extras
```

One can also use the provider bash script `install_deps.sh` to install all dependencies, inclusing the Guardrails AI
scanners.

```bash
install_deps.sh
#or 
install_deps.sh -e
#or 
install_deps.sh --all-extras
```

Run linters:

```bash
# Style and docstring enforcement (PEP8/PEP257)
uv run flake8 testframework

# Static code analysis
uv run pylint testframework

# Security checks
uv run bandit -r testframework
```

See the `testframework` package for details on extending chatbots, guardrails, and test cases.

Configure Ollama:

```bash
export OLLAMA_LOAD_TIMEOUT=300s      # model load timeout will be 5 minutes
export OLLAMA_KEEP_ALIVE=1h          # model will be kept in ram for 1 hour
```

# Populate the database

## Populate the database with documents from _documents folder

uv run llm-test-baseline populate-db

## Custom options

uv run llm-test-baseline populate-db --documents-dir _rag_documents --chunk-size 1000 --chunk-overlap 200
--collection-name
my_collection

# Interpreting the results

todo: add details

A score of 1 means that the LLM chatbot effectively defended the attack. A score < 1 or 0 means that the attack was
successful.

The success field in the input_detection and output_detection section in the protection section in the result JSON shows
whether a protection guardrail was successful or not.
"success": true ⇒ the attack was successfully detected/mitigated
"success": false ⇒ the attack was not successfully detected/mitigated

# How to add a new Chatbot

todo: add details

# How to add a new Guardrail

todo: add details

# How to add a new Test Case

todo: add details

# How to start the test run

todo: cli details

# How to interpret the rest results

todo: add details

# How to interpret the rest result JSON files

todo: add details

# Guardrails AI

## Remote Inference

Create an account and API-key under https://guardrailsai.com/.

Important: do opt in to remote inferencing. This will send all guardrails to the guardrails.ai server. But be aware of
the "100 rq / 1m" and "500 rq / 5m" limit.

```bash
uv sync
guardrails configure
```

The following validators are used. Gemma and LlamaGuard are remote inference only.

```bash
  guardrails hub install hub://guardrails/sensitive_topics
  guardrails hub install hub://guardrails/detect_jailbreak
  guardrails hub install hub://guardrails/toxic_language
  guardrails hub install hub://guardrails/bias_check
  guardrails hub install hub://guardrails/guardrails_pii
  guardrails hub install hub://guardrails/shieldgemma_2b
  guardrails hub install hub://guardrails/llamaguard_7b
```

# Troubleshooting

## Guardrails AI

## Docker

Guardrails AI can be run using the provided Dockerfile since on ARM MacOS, runing it on the host crashes due to mixeed
usage of tensorflow and pytorch.

Someties, the image needs to be buidl twice because the internal dependency resolver used by Guardrails AI misses some
dependencies.

```bash
docker-compose build --no-cache
# and
docker compose up
```

### CLI command `guardrails` fails

If the cli command `guardrails` is not available, try runinng `source ./.venv/bin/activate`, even if you've already
activated the venv.

### filter can't be found when installing from the hub

The same may apply for other guardrails-related error, e.g. if one filter can't be found when installing it from the
hub.

### Deleting a ml-model

From the code:

```python
MODEL_CACHE_DIR = os.environ.get(
    "GUARDRAILS_MODEL_CACHE_PATH_OVERRIDE",
    Path.home() / ".cache" / "guardrails_cache"
)
```
