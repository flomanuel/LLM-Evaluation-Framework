# Security Evaluation Tool for LLM Architectures and Guardrails

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![GitHub Release](https://img.shields.io/github/v/release/flomanuel/LLM-Evaluation-Framework)

This repository contains a **test framework for evaluating LLM-architectures** and guardrail applications. It is based
on work I did as a part of my bachelor's thesis, but has since evolved into a standalone project.

![Project Banner](./_extras/doc/banner.jpeg)

## Key characteristics

- **Architecture-first design**: Built around reusable core components such as `BaseChatbot`, `Test`, `BaseTestCase`,
  `GuardrailRunner`, `BaseGuardrail`, and `ChatbotStore`.
- **Adversarial attack generation with an internal red-team layer**: Uses project-owned vulnerability builders,
  custom CSV-based inputs, and single-turn attack strategies to generate and refine prompts.
- **PostgreSQL persistence**: Test runs, attack results, guardrail evaluations, and confusion-matrix summaries are
  stored in a dedicated `evaluation` schema, in its own Postgres database, via SQLAlchemy 2.0 + Alembic migrations.
  This is a separate database instance from the langchain RAG vector store. Historical JSON runs can be imported
  with `import-runs`.
- **CLI-first workflow**: Run evaluations and post-processing through dedicated CLI commands.
- **REST API**: The same functionality is exposed over HTTP via a FastAPI app
  (`uv run llm-test-baseline serve`), so a frontend can start runs, poll their status, and
  read/download results without shelling out to the CLI.
- **Extensible framework**
    - Integrate additional attack data sources \(APIs, CSV, or custom providers\).
    - Evaluate any target system \(single LLMs, multimodel pipelines, or agentic architectures on local or cloud
      infrastructure\).
    - Add custom attack techniques, scoring logic, and evaluation criteria.

## One note on the architecture

This framework relies heavily on DeepEval together with project-owned red-team modules.

DeepEval is developed by [Confident AI](https://www.confident-ai.com/docs).
The project-owned red-team modules are maintained in this repository.

## Quickstart

Note: under _extras, a simple frontend for interacting with the REST API is available. See
the [subpage](./_extras/frontend/README.md) for details.

### Local (uv)

1. Install dependencies:

```bash
uv sync
```

2. Configure environment variables:

```bash
cp .env.template .env
# Edit .env and fill in your values.
```

3. Start the infrastructure (two PostgreSQL instances — one for the RAG vector store, one for the ORM/evaluation
   data — + pgAdmin):

```bash
docker compose up -d
```

4. Apply database migrations (first time and after upgrades):

```bash
uv run alembic upgrade head
```

5. Run the baseline test suite:

```bash
uv run llm-test-baseline run-baseline
```

Each completed run is automatically persisted to the database and a confusion-matrix summary
is computed and stored.

6. (Optional) Summarize a specific run by ID:

```bash
uv run llm-test-baseline summarize-run --run-id <uuid>
```

7. (Optional) Import historical JSON runs from `_runs/`:

```bash
uv run llm-test-baseline import-runs --runs-dir _runs
```

8. (Optional) Start the REST API instead of using the CLI directly:

```bash
uv run llm-test-baseline serve
# Interactive docs: http://127.0.0.1:8000/docs
```

See [REST API](./_extras/doc/development.md#rest-api) for the full route table and design notes.

### Docker (fully containerized)

All services, including the test runner, are managed by docker-compose.
Run data is written to host directories via bind mounts — nothing is lost when containers stop.

```bash
# Start infrastructure
docker compose up -d

# Build the testframework image
docker compose build testframework

# Apply database migrations (first time and after upgrades)
docker compose run --rm testframework migrate

# Populate the vector store
docker compose run --rm testframework populate-db --documents-dir _rag_documents

# Run the baseline test suite (results are persisted to DB automatically)
docker compose run --rm testframework run-baseline --results-dir _runs

# Summarise a run by UUID (reads from and writes to the DB). This step is executed automatically on run completion (e.g. run-baseline).
docker compose run --rm testframework summarize-run --run-id <uuid>

# Import historical JSON runs from _runs/ into the DB
docker compose run --rm testframework import-runs --runs-dir _runs
```

The REST API runs as its own long-running `api` service (unlike `testframework`, it is
**not** under `profiles: [run]`, so `docker compose up -d` starts it too):

```bash
docker compose up -d api
curl http://localhost:8000/api/v1/health/liveness
```

# Running the unit tests

The unit test suite lives in the `tests/` directory and uses [pytest](https://docs.pytest.org/).
All external services (Ollama, OpenAI, GCP, Lakera, LLM Guard, LlamaFirewall) are mocked — no real credentials or
running models are required.

**Note:** Tests under `tests/persistence/` use [Testcontainers](https://testcontainers-python.readthedocs.io/) to spin
up a real Postgres instance automatically. A working Docker daemon is required to run these tests. If Docker is
unavailable, set `POSTGRES_TEST_URL` to an existing PostgreSQL connection URL to skip container startup.

Tests under `tests/api/` drive the real FastAPI `app` through `TestClient` with the service layer mocked —
no Docker or database required.

Run all tests:

```bash
uv run pytest tests/ -v
```

Run only the persistence integration tests:

```bash
uv run pytest tests/persistence/ -v
```

Run a single file:

```bash
uv run pytest tests/reporting/test_run_summary.py -v
```

Run tests matching a keyword:

```bash
uv run pytest tests/ -v -k "guardrail"
```

# Details on development

See the [subpage](./_extras/doc/development.md).

# Guardrail config and details

See the [subpage](./_extras/doc/guardrails.md).

# Generating and interpreting the result summary

After a run completes, a confusion-matrix summary is automatically computed and written to the `analysis_run` table
in the database. You can also trigger it manually:

```bash
uv run llm-test-baseline summarize-run --run-id <uuid>
```

The summary aggregates results per chatbot, per guardrail, per attack category, and per attack technique into
true-positive / false-positive / true-negative / false-negative counts.

## Interpreting scores and detection results

**Chatbot score** — a value between 0 and 1 produced by the LLM-as-a-Judge evaluation metric:

- `1.0` — the chatbot successfully defended the attack (safe response).
- `< 1.0` / `0.0` — the attack was successful (the chatbot produced an unsafe response).

**Guardrail `success` field** — present in `input_detection` and `output_detection` inside the `protection` object:

- `"success": true` — the guardrail correctly detected or mitigated the attack.
- `"success": false` — the guardrail did not detect/mitigate the attack.

**Confusion-matrix labels** — used in the summary rows stored in `summary_row`:

- Unsafe prompt + guardrail detected it → **TP** (true positive).
- Unsafe prompt + guardrail missed it → **FN** (false negative).
- Safe prompt + guardrail blocked it → **FP** (false positive, over-blocking).
- Safe prompt + guardrail passed it → **TN** (true negative).

# Troubleshooting

See the [subpage](./_extras/doc/troubleshooting.md).

# Disclaimers

Please note that this project may use Third-Party Services (including model providers and evaluation tools), which are
subject to their own terms and conditions and are not developed or verified by the authors and contributors of this
project.

Developers are responsible for implementing appropriate safeguards to prevent storage or misuse of sensitive or
prohibited content (including but not limited to personal data, child sexual abuse material, or other illegal content).
The authors and contributors of this project disclaim liability for any logging or retention of such content by
developers. Developers must ensure their systems comply with all applicable data protection and content safety laws and
should avoid persisting with any blocked content generated or intercepted by this project. This project calls paid APIs,
and developers are responsible for associated charges.
