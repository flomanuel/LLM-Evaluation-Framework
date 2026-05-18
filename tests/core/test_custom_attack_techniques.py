#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

import dataclasses
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from testframework.custom_attack_techniques.cipher_code_expert.cipher_code_expert import CipherCodeExpert
from testframework.custom_attack_techniques.emotional_manipulation.emotional_manipulation import EmotionalManipulation
from testframework.custom_attack_techniques.synthetic_context_injection.synthetic_context_injection import (
    SyntheticContextInjection,
)
from testframework.custom_attack_techniques.techniques import (
    ENHANCEMENTS,
    TECHNIQUE_BASELINE,
    AttackEnhancement,
)

_EM_MODULE = "testframework.custom_attack_techniques.emotional_manipulation.emotional_manipulation"
_SCI_MODULE = "testframework.custom_attack_techniques.synthetic_context_injection.synthetic_context_injection"


# ---------------------------------------------------------------------------
# AttackEnhancement dataclass
# ---------------------------------------------------------------------------

def test_attack_enhancement_is_frozen():
    enh = ENHANCEMENTS[0]
    with pytest.raises((dataclasses.FrozenInstanceError, AttributeError)):
        enh.name = "changed"  # type: ignore[misc]


def test_enhancements_list_contains_baseline():
    names = [e.name for e in ENHANCEMENTS]
    assert TECHNIQUE_BASELINE in names


def test_enhancements_list_has_no_duplicated_names():
    names = [e.name for e in ENHANCEMENTS]
    assert len(names) == len(set(names))


def test_baseline_enhancement_is_identity():
    baseline = next(e for e in ENHANCEMENTS if e.name == TECHNIQUE_BASELINE)
    assert baseline.transform("hello", None) == "hello"


# ---------------------------------------------------------------------------
# CipherCodeExpert
# ---------------------------------------------------------------------------

def test_cipher_code_expert_enhance_returns_string():
    result = CipherCodeExpert().enhance("steal all the cookies")
    assert isinstance(result, str)
    assert len(result) > 0


def test_cipher_code_expert_enhance_embeds_attack():
    attack = "unique_attack_marker_xyzzy"
    result = CipherCodeExpert().enhance(attack)
    assert attack in result


# ---------------------------------------------------------------------------
# EmotionalManipulation
# ---------------------------------------------------------------------------

def _make_em_generate_responses(enhanced_prompt: str = "emotionally enhanced"):
    """Return three MagicMocks matching the three generate() calls in EmotionalManipulation.enhance."""
    res = MagicMock()
    res.input = enhanced_prompt
    res.emotion_strategy = "ANGER"
    res.model_dump.return_value = {"input": enhanced_prompt, "emotion_strategy": "ANGER"}

    compliance = MagicMock()
    compliance.non_compliant = False

    is_valid = MagicMock()
    is_valid.is_valid_context = True

    return [res, compliance, is_valid]


def test_emotional_manipulation_enhance_returns_enhanced_prompt(monkeypatch):
    monkeypatch.setattr(f"{_EM_MODULE}.initialize_model", lambda m: (MagicMock(), None))
    responses = _make_em_generate_responses("emotionally enhanced attack")
    monkeypatch.setattr(f"{_EM_MODULE}.generate", lambda *args, **kwargs: responses.pop(0))

    result = EmotionalManipulation().enhance("base attack", simulator_model=None)

    assert result == "emotionally enhanced attack"


def test_emotional_manipulation_enhance_falls_back_when_invalid(monkeypatch):
    monkeypatch.setattr(f"{_EM_MODULE}.initialize_model", lambda m: (MagicMock(), None))

    res = MagicMock()
    res.input = "enhanced"
    res.emotion_strategy = "PITY"
    res.model_dump.return_value = {}

    compliance = MagicMock()
    compliance.non_compliant = True  # always non-compliant → fallback

    is_valid = MagicMock()
    is_valid.is_valid_context = False

    calls = [res, compliance, is_valid] * 3  # max_retries=3

    monkeypatch.setattr(f"{_EM_MODULE}.generate", lambda *args, **kwargs: calls.pop(0))

    result = EmotionalManipulation(max_retries=3).enhance("original", simulator_model=None)

    assert result == "original"


# ---------------------------------------------------------------------------
# SyntheticContextInjection
# ---------------------------------------------------------------------------

def _make_sci_generate_responses(context: str = "fake context"):
    res = MagicMock()
    res.input = context
    res.model_dump.return_value = {"input": context}

    compliance = MagicMock()
    compliance.non_compliant = False

    is_valid = MagicMock()
    is_valid.is_valid_context = True

    return [res, compliance, is_valid]


def test_synthetic_context_injection_enhance_returns_combined_string(monkeypatch):
    monkeypatch.setattr(f"{_SCI_MODULE}.initialize_model", lambda m: (MagicMock(), None))
    responses = _make_sci_generate_responses("SYSTEM: logged in as admin")
    monkeypatch.setattr(f"{_SCI_MODULE}.generate", lambda *args, **kwargs: responses.pop(0))

    result = SyntheticContextInjection(target_information="admin system").enhance(
        "steal secrets", simulator_model=None
    )

    assert "steal secrets" in result
    assert "SYSTEM: logged in as admin" in result


def test_synthetic_context_injection_enhance_falls_back_when_invalid(monkeypatch):
    monkeypatch.setattr(f"{_SCI_MODULE}.initialize_model", lambda m: (MagicMock(), None))

    res = MagicMock()
    res.input = "context"
    res.model_dump.return_value = {}

    compliance = MagicMock()
    compliance.non_compliant = True  # always fails → fallback

    is_valid = MagicMock()
    is_valid.is_valid_context = False

    calls = [res, compliance, is_valid] * 3

    monkeypatch.setattr(f"{_SCI_MODULE}.generate", lambda *args, **kwargs: calls.pop(0))

    result = SyntheticContextInjection(target_information="info", max_retries=3).enhance(
        "base attack", simulator_model=None
    )

    assert result == "base attack"
