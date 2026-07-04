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

3. Start infrastructure containers via Docker Compose

```bash
# Start postgres and pgadmin (background)
docker compose up -d
```

The `testframework` service is excluded from `docker compose up` intentionally (it uses
`profiles: [run]`). Invoke it explicitly — see [Docker workflow](#docker-workflow) below.

## Populate the database

Populate the database with PDF documents from `_rag_documents`.
The resulting chunks can be inspected via the pgAdmin container.

Local:
```bash
uv run llm-test-baseline populate-db --documents-dir _rag_documents
```

Docker:
```bash
docker compose run --rm testframework populate-db --documents-dir _rag_documents
```

## Docker workflow

Two Dockerfiles are provided:

| File | Purpose |
|---|---|
| `Dockerfile.guardrails` | Guardrails AI API server (used by the `guardrails_ai` compose service) |
| `Dockerfile.testframework` | `llm-test-baseline` CLI (used by the `testframework` compose service) |

Build the testframework image:
```bash
docker compose build testframework
```

Run CLI commands inside the container (results are written to host-mounted directories):
```bash
# Apply DB migrations (first time and after upgrades)
docker compose run --rm testframework migrate

# Run the baseline test suite
docker compose run --rm testframework run-baseline --results-dir _runs

# Summarize a run by UUID (primary path — reads from and writes to the DB)
docker compose run --rm testframework summarize-run --run-id <uuid>

# Summarize from a legacy JSON run folder (secondary path)
docker compose run --rm testframework summarize-run \
  --run _runs/<timestamp>_baseline \
  --output _runs/_outputs/summary.json

# Import historical JSON run folders into the DB
docker compose run --rm testframework import-runs --runs-dir _runs
```

## Persistence layer

Test results are stored in PostgreSQL under the `evaluation` schema (separate from the `public` pgvector schema used for RAG).

### Package layout

```
testframework/persistence/
  session.py          — SQLAlchemy sessionmaker; patched by test fixtures
  importer.py         — import_runs(): walks _runs/*/result.json, tolerant deserializer
  entity/             — SQLAlchemy 2.0 MappedAsDataclass ORM entities
  repository/         — TestRunRepository, AnalysisRepository, mapper.py (DTO ↔ entity)
  service/            — TestRunService (save run), AnalysisService (compute + store summary)
  model/              — Pydantic v2 input models for a future API layer
```

### Migrations

Managed with Alembic. The `alembic/env.py` targets the `evaluation` schema only and never touches `public`.

```bash
# Apply all pending migrations
uv run llm-test-baseline migrate
# or directly via Alembic
uv run alembic upgrade head
```

### Importing historical runs

JSON run folders under `_runs/` can be imported into the DB:

```bash
uv run llm-test-baseline import-runs --runs-dir _runs
# --force      re-import runs that are already in the DB (deletes existing record first)
# --no-reanalyze  skip computing analysis_run rows after import
```

The importer handles legacy enum formats (`"Category.ILLEGAL_ACTIVITY"`) and missing optional fields.

## One note on the architecture

This framework relies on DeepEval together with project-owned red-team modules.

DeepEval is developed by [Confident AI](https://www.confident-ai.com/docs).
The project-owned red-team modules are maintained in this repository.

## Terminology contract

The framework uses these terms consistently across generation, enhancement, persistence, and reporting:

1. Technique:
   A transformation strategy that can enhance a base prompt.

2. Base prompt:
   The prompt before technique enhancement, created from template generation or CSV rows.

3. Prompt/attack:
   The final prompt variant after enhancement, which is executed against the chatbot stack.

### Indirect document-embedded exception

For `document-embedded-instructions`, the CSV rows / PDFs already contain pre-enhanced prompt/attack text plus a technique label.
Those rows are treated as final prompts/attacks and are not re-enhanced at runtime.

### Baseline marker policy

`Baseline Prompt (no Technique)` is a reporting marker that means "no enhancement technique applied".
It is stored in technique buckets for consistency, even though it is not a transformation.

### Versioning note

Historical run artifacts may contain older wording around baseline/no-technique handling.
When comparing old and new summaries, treat this terminology contract as the canonical interpretation.

## Test Runs

### What is a test run

A test run is defined as a child class of the [BaseTest](../../testframework/tests/base_test.py). Currently, there is only one test run defined (DefaultTest).

One can define as many test runs as needed. Each test run must be registered in the CLI class, if it should be callable via the CLI.

Each test run defines which test cases (attack- or test-categories) should be run and which LLMs or LLM architectures should be evaluated against the tests / attacks.

Thus, one might define a first test case that thematically focusses on PII and data leakage of an LLM-chatbot and a second test case that evaluates the agentic behaviour of an agentic office system.

### How to add a new test run

To add a new test run, create a class that inherits from the abstract class BaseTest. Then, simply implement the abstract methods and you are ready to go.

## How to add a new Chatbot

A chatbot can be anything from a local LLM up to an agentic system hosted on a hyperscaler.

As of today, there are two chatbots implemented. One LLM chatbot with RAG and a dummy image genration tool and one dummy chatbot that does not require any remote infrence API. The first one uses LangChain.

One might create a new catbot by adding a class that inherits from the abstract base class [BaseChatbot](../../testframework/chatbots/base.py). Then, implement the abstract methods and add the chatbot to one of the defined test runs.

The internal implementation of the chatbot is completely up to the developer. One might access e.g. a local LLM or implement a remote REST or GraphQL API.

If a chatbot should be part of a run, then it needs to be registered in the [chatbot store](../../testframework/chatbots/store.py).

## How to add a new Guardrail

Guardrails are completely optional. They were originally developed as part of the thesis from which this project originated.

Active Guardrails must be registered in the [guardail runner](../../testframework/guardrails/runner.py).

To add a new guardrail, create a class that inherits from the [BaseGuadrail](../../testframework/guardrails/base.py). Implement the abstract methods and you are ready to go.

## How to add a new Test Case

A test case describes one category of tests (e.g. attacks) that should be executed. A test case can contain 0..N subcategories, called types.

Each test case defines a metric that should be used for evaluating the success of the test. Currently, this metric is an instance of a DeepEval metric.

All test cases require some logic to create the actual baseline test data (i.e. the prompts). This is mostly handled by builder classes but is not limited to them. Therefore, the source for the test data is not hardwired and the developer has the complete control over it. Thus, one might create a first test case that pulls the required data from remote APIs and a second one that combines data from a local CSV file with data generated by an uncensored LLM.

To create a new test case, add a class that inherits from the [BaseTestCase](../../testframework/testcases/base.py) and that implements the abstract methods.

## How to add a new technique and metric

One can use project-owned techniques or implement additional custom techniques. Each technique that should be enabled must be added to the list [ENHANCEMENTS](../../testframework/custom_attack_techniques/techniques.py), which defines all techniques that the [AttackListEnhancer](../../testframework/custom_attack_techniques/attack_list_enhancer.py) will apply to the baseline test data.

Each custom technique must be an instance of [BaseSingleTurnAttack](../../testframework/redteam/techniques/base.py).
