# Security Evaluation Tool for LLM Architectures and Guardrails

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![GitHub Release](https://img.shields.io/github/v/release/flomanuel/LLM-Evaluation-Framework)

This repository contains a **test framework for evaluating LLM-architectures** and guardrail applications. It is based on work I did as a part of my bachelor's thesis, but has since evolved into a standalone project.

![Project Banner](./_extras/doc/banner.jpeg)

## Key characteristics

- **Architecture-first design**: Built around reusable core components such as `BaseChatbot`, `Test`, `BaseTestCase`,
  `GuardrailRunner`, `BaseGuardrail`, and `ChatbotStore`.
- **Adversarial attack generation with an internal red-team layer**: Uses project-owned vulnerability builders,
  custom CSV-based inputs, and single-turn attack strategies to generate and refine prompts.
- **PostgreSQL persistence**: Test runs, attack results, guardrail evaluations, and confusion-matrix summaries are
  stored in a dedicated `evaluation` schema via SQLAlchemy 2.0 + Alembic migrations. Historical JSON runs can be
  imported with `import-runs`.
- **CLI-first workflow**: Run evaluations and post-processing through dedicated CLI commands.
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

3. Start the infrastructure (PostgreSQL + pgAdmin):

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

# Summarise a run by UUID (reads from and writes to the DB)
docker compose run --rm testframework summarize-run --run-id <uuid>

# Import historical JSON runs from _runs/ into the DB
docker compose run --rm testframework import-runs --runs-dir _runs
```

# Running the unit tests

The unit test suite lives in the `tests/` directory and uses [pytest](https://docs.pytest.org/).
All external services (Ollama, OpenAI, GCP, Lakera, LLM Guard, LlamaFirewall) are mocked — no real credentials or
running models are required.

**Note:** Tests under `tests/persistence/` use [Testcontainers](https://testcontainers-python.readthedocs.io/) to spin
up a real Postgres instance automatically. A working Docker daemon is required to run these tests. If Docker is
unavailable, set `POSTGRES_TEST_URL` to an existing PostgreSQL connection URL to skip container startup.

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

# Generating and analyzing the result summary

# Interpreting the results

todo: add details

A score of 1 means that the LLM chatbot effectively defended the attack. A score < 1 or 0 means that the attack was
successful.

The success field in the input_detection and output_detection section in the protection section in the result JSON shows
whether a protection guardrail was successful or not.
"success": true ⇒ the attack was successfully detected/mitigated
"success": false ⇒ the attack was not successfully detected/mitigated

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
