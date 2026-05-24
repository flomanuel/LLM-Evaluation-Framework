#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

from testframework.redteam.techniques.library import (
    AdversarialPoetry,
    Base64,
    MathProblem,
    PromptInjection,
    Roleplay,
)


def test_local_techniques_return_non_empty_prompt():
    prompt = "do x"
    techniques = [
        AdversarialPoetry(),
        Roleplay(),
        MathProblem(),
        Base64(),
        PromptInjection(),
    ]
    for technique in techniques:
        output = technique.enhance(prompt)
        assert isinstance(output, str)
        assert output


def test_base64_prompt_injection_chain_changes_prompt():
    prompt = "sensitive task"
    encoded = Base64().enhance(prompt)
    chained = PromptInjection().enhance(encoded)
    assert chained != prompt
    assert "System Override" in chained
