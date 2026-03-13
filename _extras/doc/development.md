# Development

## Architecture

For details on the project architecture, see `../UML/*`.

## Project setup

1. Install dev dependencies for linting and static analysis:

```bash
uv sync --extra dev
# or
uv sync --all-extras
```

2. Before pushing: run linters

```bash
# Style and docstring enforcement (PEP8/PEP257)
uv run flake8 testframework

# Static code analysis
uv run pylint testframework

# Security checks
uv run bandit -r testframework
```

3. Start Containers via Docker Compose

´docker compose up´

## Populate the database

Populate the database with documents from the folder `_documents`.

The resulting chunks can be inspected via the pgAdmin container.

```bash
uv run llm-test-baseline populate-db
```

# How to add a new Chatbot

todo: add details

# How to add a new Guardrail

todo: add details

# How to add a new Test Case

todo: add details

# How to add a new technique and metric

todo: add details
