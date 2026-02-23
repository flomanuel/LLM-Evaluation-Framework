# thesis_llm-chatbot_protection

This repository contains a **test framework for evaluating guardrail applications for LLM chatbots** as part of a bachelor's thesis.

Key characteristics:

- **Architecture-driven**: Follows a modular architecture with `BaseChatbot`, `Test`, `BaseTestCase`, `GuardrailRunner`, `BaseGuardrail`, and `ChatbotStore`.
- **Attack generation with DeepTeam**: Uses DeepTeam vulnerabilities (including a custom CSV-based vulnerability) and single-turn adversarial attacks to generate and enhance prompts.
- **Result schema**: Persists each test run as a JSON file containing categories, attacks, RAG context, LLM parameters/responses, and guardrail evaluation results.

## Quickstart

1. Install dependencies (using `uv`):

```bash
uv sync
```

2. Run the baseline test suite (once implemented):

```bash
uv run llm-test-baseline run-baseline
```

3. Configure your OpenAI API key (for example):

```bash
export OPENAI_API_KEY="sk-..."
```

See the `testframework` package for details on extending chatbots, guardrails, and test cases.

