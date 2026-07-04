# Project notes for Claude Code

## What this project is

A test framework for evaluating LLM architectures and guardrail applications.
It generates adversarial attacks, runs them against chatbots and guardrails, and persists
results to PostgreSQL for analysis. Originally a bachelor's thesis project; now a standalone tool.

## Repository structure

- `testframework/` — framework source code
- `tests/` — unit and integration tests (external services mocked)
- `_rag_documents/` — source PDFs for RAG evaluation scenarios
- `_attack_documents/` — attack documents and adversarial fixtures
- `_prompt_files/` — CSV prompt inputs
- `_runs/` — generated run artifacts (JSON result files)
- `_logs/` — log output
- `_extras/` — supporting documentation and UML diagrams
- `Dockerfile.guardrails` — Docker image for the Guardrails AI API server
- `Dockerfile.testframework` — Docker image for the `llm-test-baseline` CLI
- `docker-compose.yml` — orchestrates postgres, pgadmin, and testframework services
- `alembic/` — migration scripts (targets the `evaluation` schema only)

## Key architecture decisions

### Persistence layer (`testframework/persistence/`)

- **ORM**: SQLAlchemy 2.0 `MappedAsDataclass` + `DeclarativeBase`. All entities live in the
  `evaluation` schema (separate from the `public` pgvector schema).
- **Schema**: Configured via `POSTGRES_SCHEMA` env var (default: `evaluation`).
  `session.py` reads this at import time; entities reference `POSTGRES_SCHEMA` in
  `__table_args__` and FK strings.
- **Migrations**: Alembic. Run `alembic upgrade head` before first use.
  The `alembic/env.py` filters to `evaluation` schema only — it never touches `public`.
- **MappedAsDataclass FK footgun**: `init=False, default=None` relationships are set LAST
  by the dataclass `__init__`, which can null out FK columns during flush. Workaround:
  explicitly assign the relationship object on the entity before flushing.
  See `AnalysisService.summarize_and_store` for the pattern.

### DTO ↔ Entity mapping (`testframework/persistence/repository/mapper.py`)

Single source of truth for converting between `models.py` DTOs and ORM entities.
Functions are named `<thing>_to_entity` / `<thing>_from_entity`.
- Avoid naming mapper functions `test_*` — pytest collects them.

### Service layer

- `TestRunService` — transaction boundaries; DTO→entity orchestration.
- `AnalysisService` — loads run from DB, computes confusion-matrix summary via
  `RunSummary._build_from_dict`, persists `analysis_run` + rows.
- Services use `import testframework.persistence.session as _session_mod` (module reference,
  not direct import) so test fixtures can override `_session_mod.Session`.

### RunSummary (`testframework/reporting/run_summary.py`)

Core aggregation logic. Two entry points:
- `build()` — reads `testcase/*.json` files (legacy path, still used for the CLI `--run` flag).
- `build_from_testcases(testcases)` — works on a list of dicts (same shape as JSON files).
- `_build_from_dict(run_dict)` — classmethod; used by `AnalysisService` to go from DTO→dict→summary.

### Importer (`testframework/persistence/importer.py`)

Reads `_runs/*/result.json` (historical format). `deserialize_run()` is tolerant:
handles `"Category.ILLEGAL_ACTIVITY"` legacy enum strings, missing optional fields,
`PromptHardeningDetectionElement` detection with embedded `chatbot_response`, etc.

### Pydantic models (`testframework/persistence/model/`)

Input models for a future API layer. Each has `to_entity()`. No routers exist yet.

## Running tests

```bash
uv run pytest tests/        # full suite (requires Docker for Testcontainers)
uv run pytest tests/core/ tests/reporting/   # no Docker needed
uv run pytest tests/persistence/             # needs Docker
```

Persistence tests use `tests/persistence/conftest.py` which starts a `postgres:16` container
via Testcontainers, runs `alembic upgrade head`, and patches `_session_module.Session`.

## CLI commands

```bash
uv run llm-test-baseline migrate              # alembic upgrade head
uv run llm-test-baseline run-baseline         # execute test suite, persist to DB
uv run llm-test-baseline summarize-run --run-id <uuid>
uv run llm-test-baseline import-runs --runs-dir _runs [--force] [--no-reanalyze]
uv run llm-test-baseline populate-db --documents-dir _rag_documents
```

## Models and enums

Core data model lives in `testframework/models.py` (dataclasses).
Enums live in `testframework/enums.py` (`Category`, `ChatbotName`, `Severity`, `CliArgs`).
All model dataclasses use `@dataclass(eq=False, slots=True, kw_only=True)` — all constructor
calls must use keyword arguments.

## Development guidance

- Keep changes scoped to the existing package structure in `testframework/`.
- Prefer existing CLI and model abstractions over introducing new entry points.
- Treat external integrations as boundary code; keep unit tests mocked rather than depending on live services.
- Do not commit generated run data, local database state, secrets, or environment-specific artifacts.
- Commit messages follow the Conventional Commits format.

## Validation

- For code changes, run the narrowest relevant pytest scope first.
- Broaden to `uv run pytest tests/ -v` when shared behavior or public interfaces are affected.
- If CLI behavior changes, validate the corresponding `llm-test-baseline` command path.

## Additional notes

Use lazy logging.
