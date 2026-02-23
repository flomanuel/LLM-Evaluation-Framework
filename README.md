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

# Populate database with documents from _documents folder
llm-test-baseline populate-db

# Custom options
llm-test-baseline populate-db --documents-dir _documents --chunk-size 1000 --chunk-overlap 200 --collection-name my_collection
