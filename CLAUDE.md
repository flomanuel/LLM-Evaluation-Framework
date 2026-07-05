# Project notes for Claude Code

## What this project is

A test framework for evaluating LLM architectures and guardrail applications.
It generates adversarial attacks, runs them against chatbots and guardrails, and persists
results to PostgreSQL for analysis. Originally a bachelor's thesis project; now a standalone tool.

## Repository structure

- `testframework/` — framework source code
  - `api/` — FastAPI REST API (routers, app factory, uvicorn server) — see below
- `tests/` — unit and integration tests (external services mocked)
- `_rag_documents/` — source PDFs for RAG evaluation scenarios
- `_attack_documents/` — attack documents and adversarial fixtures
- `_prompt_files/` — CSV prompt inputs
- `_runs/` — generated run artifacts (JSON result files)
- `_logs/` — log output
- `_extras/` — supporting documentation and UML diagrams
- `Dockerfile.guardrails` — Docker image for the Guardrails AI API server
- `Dockerfile.testframework` — Docker image for the `llm-test-baseline` CLI
- `docker-compose.yml` — orchestrates `postgres_rag`, `postgres_eval`, pgadmin, and testframework services
- `alembic/` — migration scripts (targets the `evaluation` schema in the ORM database only)

## Key architecture decisions

### Two separate databases

The ORM (evaluation) data and the langchain RAG vector store live in **separate Postgres
instances**, each with its own container and env var family:

- `postgres_rag` (`pgvector/pgvector:pg16`) — langchain `PGVector` tables
  (`langchain_pg_embedding`, `langchain_pg_collection`). Configured via `POSTGRES_HOST`,
  `POSTGRES_PORT`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`. Used only by
  `testframework/chatbots/rag/vector_store.py`.
- `postgres_eval` (`postgres:16`, no pgvector needed) — all SQLAlchemy/Alembic entities.
  Configured via `EVAL_DB_HOST`, `EVAL_DB_PORT`, `EVAL_DB_USER`, `EVAL_DB_PASSWORD`,
  `EVAL_DB_NAME`. Used by `testframework/persistence/session.py` and `alembic/env.py`.

Do not let these two connection configs bleed into each other — they intentionally point
at different databases.

### Persistence layer (`testframework/persistence/`)

- **ORM**: SQLAlchemy 2.0 `MappedAsDataclass` + `DeclarativeBase`. All entities live in the
  `evaluation` schema, inside the dedicated `postgres_eval` database (see above) — this
  schema layer is kept for organizational clarity even though the DB is already isolated.
- **Schema**: Configured via `POSTGRES_SCHEMA` env var (default: `evaluation`).
  `session.py` reads this at import time; entities reference `POSTGRES_SCHEMA` in
  `__table_args__` and FK strings.
- **Migrations**: Alembic. Run `alembic upgrade head` before first use.
  `alembic/env.py` connects to `postgres_eval` via the `EVAL_DB_*` env vars and filters
  to the `evaluation` schema only.
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

Input models used by the API layer where relevant. Each has `to_entity()`.
The response/read side is exclusively the `models.py` DTO dataclasses (see below) —
no separate Pydantic response schemas exist.

### REST API (`testframework/api/`)

FastAPI app exposing the test-framework functionality (previously only reachable via the
CLI) under `/api/v1`. Richardson Maturity Level 2: real resources, correct verbs/status
codes, conditional GETs via `ETag`/`If-None-Match` — no HATEOAS.

```
testframework/api/
  app.py                     — create_app() factory (CORSMiddleware, routers, exception
                                handlers); module-level `app = create_app()`
  asgi_server.py             — run() starts uvicorn against "testframework.api:app"
  constants.py               — ETAG / IF_MATCH / IF_NONE_MATCH header names
  dependencies.py            — ExistingRun / ExistingRunId: shared Depends that 404 via
                                NotFoundError when a run doesn't exist
  errors.py                  — NotFoundError (404), RunAlreadyRunningError (409) + handlers
  page.py                    — Pageable (parses ?page=&size=) and Page/PageMeta wrapper
  router/
    health_router.py            — GET /health/liveness, /health/readiness
    test_run_read_router.py     — all GET endpoints (list, single run, status, test-cases,
                                   analyses, analyses/export)
    test_run_write_router.py    — POST /test-runs (start, async), DELETE /test-runs/{id}
```

- **Responses are DTOs, not Pydantic schemas.** Every read endpoint declares
  `response_model=<DTO dataclass>` (for OpenAPI/Swagger) but actually returns a hand-built
  `JSONResponse`/`Response`, serialized via `json.loads(json.dumps(dataclasses.asdict(dto),
  default=str))` — the same idiom already used by `storage.py` and
  `AnalysisService._build_summary_from_dto`. This handles the project's `(str, Enum)` members
  and `datetime` fields without a bespoke encoder.
- **Strong ETags from real optimistic-locking columns.** `TestRunEntity.version` and
  `AnalysisRunEntity.version` are SQLAlchemy `version_id_col`s (auto-incremented on every
  UPDATE). Single-resource GETs (run, single analysis) emit `ETag: "<version>"`, pop
  `version` out of the JSON body, and return `304` on a matching `If-None-Match` — see the
  shared `_not_modified()` helper in `test_run_read_router.py`. An analysis's version never
  changes after creation, so its ETag is stable/immutable.
- **Async run execution (W1).** `POST /test-runs` pre-inserts the `test_run` row (so it can
  return a real `run_id`/`ETag` in the `202`), then schedules the real run via FastAPI
  `BackgroundTasks` (Starlette runs sync background callables through its threadpool, so the
  event loop isn't blocked). `TestRunService.start_run` is therefore **idempotent** — the
  background job's own `start_run` call (inside `Test.run()`) is then a no-op. A single
  in-flight run is enforced by `TestRunService.has_active_run()`, which checks the DB
  `status` column (`pending`/`running`/`completed`/`failed`) rather than in-process state.
- **CSV/ZIP export (R8).** `testframework/reporting/analysis_csv.py` reconstructs the
  historical per-model `summary.csv` files from stored `SummaryRow` rows (splitting the
  stored `node = "<model>/<node>"` on the first `/`) — mirrors
  `RunSummary._build_summary_csv_rows` in reverse. One ZIP folder per analysis variant:
  `consider_model_alignment/` (consider_chatbot_success=True) and `without_model_alignment/`
  (=False).
- **Route registration order matters.** `/analyses/export` (a literal path) is registered
  before `/analyses/{analysis_id}` (R7) so Starlette's first-match routing doesn't let the
  parameterized route swallow the literal one.
- **Serve it:** `uv run llm-test-baseline serve` (env `API_HOST`/`API_PORT`, default
  `127.0.0.1:8000`), or `uv run uvicorn testframework.api:app --host 0.0.0.0 --port 8000`.
  Interactive OpenAPI docs at `/docs` once running.

## Running tests

```bash
uv run pytest tests/        # full suite (requires Docker for Testcontainers)
uv run pytest tests/core/ tests/reporting/ tests/api/   # no Docker needed
uv run pytest tests/persistence/             # needs Docker
```

Persistence tests use `tests/persistence/conftest.py` which starts a `postgres:16` container
via Testcontainers, runs `alembic upgrade head`, and patches `_session_module.Session`.
`tests/api/` uses FastAPI's `TestClient` against the real `app` object with the service
classes mocked (`unittest.mock.patch` at the router/dependency import site) — no DB needed.

Note: the `tests/persistence` Postgres container is session-scoped and never cleared between
tests, so tests that need an exact row count (e.g. `TestRunRepository.find_page`) must scope
their query to a private marker value (a unique `status` string) rather than assuming a clean
table — other tests' committed rows are visible.

## CLI commands

```bash
uv run llm-test-baseline migrate              # alembic upgrade head
uv run llm-test-baseline run-baseline         # execute test suite, persist to DB
uv run llm-test-baseline summarize-run --run-id <uuid>
uv run llm-test-baseline import-runs --runs-dir _runs [--force] [--no-reanalyze]
uv run llm-test-baseline populate-db --documents-dir _rag_documents
uv run llm-test-baseline serve                # start the REST API (uvicorn)
```

## Models and enums

Core data model lives in `testframework/models.py` (dataclasses).
Enums live in `testframework/enums.py` (`Category`, `ChatbotName`, `Severity`, `RunStatus`,
`CliArgs`). All model dataclasses use `@dataclass(eq=False, slots=True, kw_only=True)` — all
constructor calls must use keyword arguments.

Read-side DTOs that mirror an entity's optimistic-lock column carry an additive
`version: int | None = None` field (`TestRunResult`, `AnalysisRunResult`) — populated by the
mapper, popped out of the JSON body by the API and carried in the `ETag` header instead.
`TestCaseResult.id` and `AnalysisRunResult.id` similarly expose the entity's PK so the API can
address single resources (R5, R7). `TestRunStatusResult` is a separate, lightweight DTO
(no nested aggregate) used only for run-list/status reads.

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
