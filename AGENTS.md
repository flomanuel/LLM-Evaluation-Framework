# AGENTS.md

## Purpose

This repository contains a Python-based evaluation framework for testing LLM chatbot guardrails and related protection architectures. The main package is `testframework`, and the primary workflow is CLI-driven.

## Working assumptions

- Python version: `>=3.13`
- Dependency manager: `uv`
- Main CLI entry point: `uv run llm-test-baseline`
- Test runner: `uv run pytest tests/ -v`

## Repository structure

- `testframework/`: framework source code
- `tests/`: unit and integration-style tests with mocked external services
- `_rag_documents/`: source documents used for RAG-related evaluation scenarios
- `_attack_documents/`: attack documents and adversarial fixtures
- `_prompt_files/`: CSV prompt inputs
- `_runs/`: generated run artifacts
- `_logs/`: log output
- `_extras/`: supporting documentation

## Setup

1. Install dependencies:
   - `uv sync`
2. Create environment file:
   - `cp .env.template .env`
3. Fill in any required credentials in `.env` before running CLI flows that depend on external providers.

## Common commands

- Run the baseline suite:
  - `uv run llm-test-baseline run-baseline`
- Summarize a run:
  - `uv run llm-test-baseline summarize-run --run <absolute_run_dir> --output <absolute_output_json>`
- Run all tests:
  - `uv run pytest tests/ -v`
- Run one test file:
  - `uv run pytest tests/test_models.py -v`
- Run a filtered test selection:
  - `uv run pytest tests/ -v -k "<pattern>"`

## Development guidance

- Keep changes scoped to the existing package structure in `testframework/`.
- Prefer existing CLI and model abstractions over introducing new entry points.
- Treat external integrations as boundary code; keep unit tests mocked rather than depending on live services.
- Do not commit generated run data, local database state, secrets, or environment-specific artifacts unless explicitly required.
- Commit messages should follow the Conventional Commits format.

## Validation expectations

- For code changes, run the narrowest relevant pytest scope first.
- Broaden to `uv run pytest tests/ -v` when shared behavior or public interfaces are affected.
- If CLI behavior changes, validate the corresponding `llm-test-baseline` command path.

## Related docs

- `README.md`
- `_extras/doc/development.md`
- `_extras/doc/guardrails.md`
- `_extras/doc/troubleshooting.md`
