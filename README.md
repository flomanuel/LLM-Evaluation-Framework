# Security Evaluation Tool for LLM Architectures and Guardrails
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![GitHub Release](https://img.shields.io/github/v/release/flomanuel/LLM-Evaluation-Framework?include_prereleases)

![Project Banner](./_extras/doc/banner.jpeg)

This repository contains a **test framework for evaluating guardrail applications for LLM-architectures**. It is part of
my bachelor's thesis.

## Key characteristics

- **Architecture-first design**: Built around reusable core components such as `BaseChatbot`, `Test`, `BaseTestCase`,
  `GuardrailRunner`, `BaseGuardrail`, and `ChatbotStore`.
- **Adversarial attack generation with DeepTeam**: Leverages DeepTeam vulnerabilities, including custom CSV-based
  vulnerabilities, and single-turn attack strategies to generate and refine prompts.
- **Structured result artifacts**: Stores each test run as JSON; a separate summarization script can aggregate runs into
  a consolidated report.
- **CLI-first workflow**: Run evaluations and post-processing through dedicated CLI commands.
- **Extensible framework**
    - Integrate additional attack data sources \(APIs, DeepTeam, CSV, or custom providers\).
    - Evaluate any target system \(single LLMs, multi-model pipelines, or agentic architectures on local or cloud
      infrastructure\).
    - Add custom attack techniques, scoring logic, and evaluation criteria.

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

4. Run the summary script

```bash
uv run llm-test-baseline summarize-run --run absolute_path_to_run_folder --output absolute_path_to_output.json
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
