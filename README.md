# [Project Banner](./_extras/doc/banner.jpeg)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

# Security Evaluation Tool for LLM-Architectures and Guardrails

This repository contains a **test framework for evaluating guardrail applications for LLM-architectures**. Is is part of my
bachelor's thesis.

## Key characteristics:

- **Architecture-driven**: Follows a modular architecture with `BaseChatbot`, `Test`, `BaseTestCase`, `GuardrailRunner`,
  `BaseGuardrail`, and `ChatbotStore`.
- **Attack generation with DeepTeam**: Uses DeepTeam vulnerabilities (including a custom CSV-based vulnerability) and
  single-turn adversarial attacks to generate and enhance prompts.
- **Result schema**: Persists each test run as a JSON file. Summary file can be added via an additional script
- **CLI based"": Interact with the Project via CLI commands
- **Modular**
  - add any data source you like for generating attacks (APIs, DeepTeam, CSV files, etc.)
  - add any LLM, LLM-based or agentic architecture as the attack target (it doesn't matter whether it is a local model or an agentic architecture hosted on a hyperscaler)
	- add your own custom techniques and evaluation criterias


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

# Details on development

See: TBD

# Guardrail config

See: TBD
