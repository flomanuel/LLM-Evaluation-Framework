#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

import pytest

from testframework.redteam.techniques.library import (
    AdversarialPoetry,
    Base64,
    MathProblem,
    PromptInjection,
    Roleplay,
)

_MODEL_BACKED = [AdversarialPoetry, Roleplay, MathProblem, PromptInjection]


def test_base64_encodes_without_model():
    prompt = "do x"
    output = Base64().enhance(prompt)
    assert isinstance(output, str)
    assert output
    assert prompt not in output


def test_base64_output_is_decodable():
    import base64
    prompt = "sensitive task"
    output = Base64().enhance(prompt)
    # The output contains the base64-encoded payload after the instruction prefix
    encoded_part = output.split("\n")[-1]
    decoded = base64.b64decode(encoded_part).decode("utf-8")
    assert decoded == prompt


def test_model_backed_techniques_raise_without_simulator_model():
    for TechniqueClass in _MODEL_BACKED:
        with pytest.raises(ValueError, match="requires a simulator model"):
            TechniqueClass().enhance("some attack", simulator_model=None)


def test_model_backed_technique_calls_generate_and_returns_input(monkeypatch):
    from testframework.redteam.generation.model_generator import TechniqueEnhancementResponse
    import testframework.redteam.techniques.library as lib

    captured: list[str] = []

    def _fake_generate(prompt, schema, model):
        captured.append(prompt)
        return TechniqueEnhancementResponse(strategy="test strategy", input="generated enhanced attack")

    monkeypatch.setattr(lib, "generate", _fake_generate)

    result = AdversarialPoetry().enhance("do x", simulator_model="mock-model")
    assert result == "generated enhanced attack"
    assert len(captured) == 1
    assert "do x" in captured[0]


def test_base64_prompt_injection_chain_requires_model_for_injection():
    encoded = Base64().enhance("sensitive task")
    assert encoded
    with pytest.raises(ValueError, match="requires a simulator model"):
        PromptInjection().enhance(encoded, simulator_model=None)


def test_prompt_injection_passes_attack_into_meta_prompt(monkeypatch):
    from testframework.redteam.generation.model_generator import TechniqueEnhancementResponse
    import testframework.redteam.techniques.library as lib

    captured: list[str] = []

    def _fake_generate(prompt, schema, model):
        captured.append(prompt)
        return TechniqueEnhancementResponse(strategy="injection strategy", input="injected prompt")

    monkeypatch.setattr(lib, "generate", _fake_generate)

    Base64().enhance("payload")
    result = PromptInjection().enhance("payload content", simulator_model="mock-model")
    assert result == "injected prompt"
    assert "payload content" in captured[0]
