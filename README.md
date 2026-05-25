# Security Evaluation Tool for LLM Architectures and Guardrails

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![GitHub Release](https://img.shields.io/github/v/release/flomanuel/LLM-Evaluation-Framework?include_prereleases)

This repository contains a **test framework for evaluating guardrail applications for LLM-architectures**. It is part of
my bachelor's thesis.

![Project Banner](./_extras/doc/banner.jpeg)

## Key characteristics

- **Architecture-first design**: Built around reusable core components such as `BaseChatbot`, `Test`, `BaseTestCase`,
  `GuardrailRunner`, `BaseGuardrail`, and `ChatbotStore`.
- **Adversarial attack generation with an internal red-team layer**: Uses project-owned vulnerability builders,
  custom CSV-based inputs, and single-turn attack strategies to generate and refine prompts.
- **Structured result artifacts**: Stores each test run as JSON; a separate summarization script can aggregate runs into
  a consolidated report.
- **CLI-first workflow**: Run evaluations and post-processing through dedicated CLI commands.
- **Extensible framework**
    - Integrate additional attack data sources \(APIs, CSV, or custom providers\).
    - Evaluate any target system \(single LLMs, multi-model pipelines, or agentic architectures on local or cloud
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

3. Start the infrastructure (PostgreSQL + pgAdmin + Guardrails AI):

```bash
docker compose up -d
```

4. Run the baseline test suite:

```bash
uv run llm-test-baseline run-baseline
```

5. Run the summary script:

```bash
uv run llm-test-baseline summarize-run --run <path_to_run_folder> --output <path_to_output.json>
```

### Docker (fully containerised)

All services including the test runner are managed by docker-compose.
Run data is written to host directories via bind mounts — nothing is lost when containers stop.

```bash
# Start infrastructure
docker compose up -d

# Build the testframework image
docker compose build testframework

# Populate the vector store
docker compose run --rm testframework populate-db --documents-dir _rag_documents

# Run the baseline test suite
docker compose run --rm testframework run-baseline --results-dir _runs

# Summarise a completed run
docker compose run --rm testframework summarize-run \
  --run _runs/<name_run_folder> \
  --output _runs/_outputs/summary.json
```

# Running the unit tests

The unit test suite lives in the `tests/` directory and uses [pytest](https://docs.pytest.org/).
All external services (Ollama, OpenAI, GCP, Lakera, LLM Guard, LlamaFirewall) are mocked — no real credentials or
running models are required.

Run all tests:

```bash
uv run pytest tests/ -v
```

Run a single file:

```bash
uv run pytest tests/test_models.py -v
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
developers. Developers must ensure their systems comply with all applicable data protection and content safety laws, and
should avoid persisting any blocked content generated or intercepted by this project. This project calls paid APIs, and
developers are responsible for associated charges.
