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
