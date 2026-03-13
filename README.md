![Project Banner](./_extras/doc/banner.jpeg)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

# Security Evaluation Tool for LLM Architectures and Guardrails

This repository contains a **test framework for evaluating guardrail applications for LLM-architectures**. Is is part of my
bachelor's thesis.

## Key characteristics

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

## One note on the architecture

This framework relies on the libraries DeepTeam and especially DeepEval.

Both are developed and maintained by [Confident AI](https://www.confident-ai.com/docs).

## Quickstart

1. Install dependencies (using `uv`):

```bash
uv sync
```

2. Configure environment variables:

```bash
cp .env.template .env
# Edit .env and fill in your values.
```

3. Run the baseline test suite:

```bash
uv run llm-test-baseline run-baseline
```

# Details on development

See the [sub page](./_extras/doc/development.md).

# Guardrail config and details

See the [sub page](./_extras/doc/guardrails.md).

# Generating and analysing the result summary

# Interpreting the results

todo: add details

A score of 1 means that the LLM chatbot effectively defended the attack. A score < 1 or 0 means that the attack was
successful.

The success field in the input_detection and output_detection section in the protection section in the result JSON shows
whether a protection guardrail was successful or not.
"success": true ⇒ the attack was successfully detected/mitigated
"success": false ⇒ the attack was not successfully detected/mitigated

# Troubleshooting

See the [sub page](./_extras/doc/troubleshooting.md).
