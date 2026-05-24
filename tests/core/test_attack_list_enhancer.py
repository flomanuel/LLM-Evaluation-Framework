#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

from types import SimpleNamespace

from testframework.custom_attack_techniques.attack_list_enhancer import AttackListEnhancer
from testframework.custom_attack_techniques.techniques import AttackEnhancement, TECHNIQUE_BASELINE
def _fake_attack(text="attack text", vulnerability_type="generic", metadata=None):
    return SimpleNamespace(
        input=text,
        vulnerability_type=vulnerability_type,
        metadata=metadata or {},
    )


def _passthrough_enhancement():
    return AttackEnhancement(
        name="fake",
        transform=lambda p, m: p + "_enhanced",
        cooldown=lambda s: None,
    )


def _failing_enhancement():
    def _raise(p, m):
        raise ValueError("boom")
    return AttackEnhancement(name="failing", transform=_raise, cooldown=lambda s: None)


# ---------------------------------------------------------------------------
# _load_error_threshold_percent
# ---------------------------------------------------------------------------

def test_load_error_threshold_uses_default_when_env_not_set(monkeypatch):
    monkeypatch.setattr(
        "testframework.custom_attack_techniques.attack_list_enhancer.load_dotenv",
        lambda **kwargs: None,
    )
    monkeypatch.delenv(AttackListEnhancer.ERROR_THRESHOLD_ENV_VAR, raising=False)
    assert AttackListEnhancer._load_error_threshold_percent() == 100.0


def test_load_error_threshold_reads_from_env(monkeypatch):
    monkeypatch.setenv(AttackListEnhancer.ERROR_THRESHOLD_ENV_VAR, "42.5")
    assert AttackListEnhancer._load_error_threshold_percent() == 42.5


def test_load_error_threshold_clamps_to_zero_when_negative(monkeypatch):
    monkeypatch.setenv(AttackListEnhancer.ERROR_THRESHOLD_ENV_VAR, "-10")
    assert AttackListEnhancer._load_error_threshold_percent() == 0.0


def test_load_error_threshold_clamps_to_hundred_when_above(monkeypatch):
    monkeypatch.setenv(AttackListEnhancer.ERROR_THRESHOLD_ENV_VAR, "150")
    assert AttackListEnhancer._load_error_threshold_percent() == 100.0


def test_load_error_threshold_falls_back_on_invalid_string(monkeypatch):
    monkeypatch.setenv(AttackListEnhancer.ERROR_THRESHOLD_ENV_VAR, "not_a_number")
    assert AttackListEnhancer._load_error_threshold_percent() == 100.0


# ---------------------------------------------------------------------------
# _load_retry_attempts
# ---------------------------------------------------------------------------

def test_load_retry_attempts_uses_default_when_env_not_set(monkeypatch):
    monkeypatch.setattr(
        "testframework.custom_attack_techniques.attack_list_enhancer.load_dotenv",
        lambda **kwargs: None,
    )
    monkeypatch.delenv(AttackListEnhancer.RETRY_ATTEMPTS_ENV_VAR, raising=False)
    assert AttackListEnhancer._load_retry_attempts() == 0


def test_load_retry_attempts_reads_from_env(monkeypatch):
    monkeypatch.setenv(AttackListEnhancer.RETRY_ATTEMPTS_ENV_VAR, "3")
    assert AttackListEnhancer._load_retry_attempts() == 3


def test_load_retry_attempts_falls_back_on_invalid_string(monkeypatch):
    monkeypatch.setenv(AttackListEnhancer.RETRY_ATTEMPTS_ENV_VAR, "not_a_number")
    assert AttackListEnhancer._load_retry_attempts() == 0


def test_load_retry_attempts_clamps_negative_to_zero(monkeypatch):
    monkeypatch.setenv(AttackListEnhancer.RETRY_ATTEMPTS_ENV_VAR, "-2")
    assert AttackListEnhancer._load_retry_attempts() == 0


# ---------------------------------------------------------------------------
# _is_error_threshold_exceeded
# ---------------------------------------------------------------------------

def test_is_error_threshold_exceeded_false_when_planned_zero():
    assert AttackListEnhancer._is_error_threshold_exceeded(0, 0, 50.0) is False


def test_is_error_threshold_exceeded_false_when_within():
    assert AttackListEnhancer._is_error_threshold_exceeded(1, 4, 50.0) is False


def test_is_error_threshold_exceeded_true_when_strictly_above():
    assert AttackListEnhancer._is_error_threshold_exceeded(3, 4, 50.0) is True


def test_is_error_threshold_exceeded_false_when_exactly_at():
    assert AttackListEnhancer._is_error_threshold_exceeded(2, 4, 50.0) is False


# ---------------------------------------------------------------------------
# enhance – no enhancements
# ---------------------------------------------------------------------------

def test_enhance_with_empty_enhancements_returns_passthrough():
    enhancer = AttackListEnhancer(simulator_model=None)
    attacks = [_fake_attack("text1"), _fake_attack("text2")]
    result = enhancer.enhance(attacks, enhancements=[])
    assert result.failed_attack_count == 0
    assert len(result.enhanced_attacks) == 2
    for ea in result.enhanced_attacks:
        assert ea.enhanced_input == ea.baseline_input


# ---------------------------------------------------------------------------
# enhance – document-embedded attacks
# ---------------------------------------------------------------------------

def test_enhance_skips_re_enhancement_for_doc_embedded_attacks():
    enhancer = AttackListEnhancer(simulator_model=None)
    attack = _fake_attack(
        text="doc attack",
        vulnerability_type="document-embedded-instructions",
        metadata={"technique": "doc_technique"},
    )
    result = enhancer.enhance([attack], enhancements=[_passthrough_enhancement()])
    assert len(result.enhanced_attacks) == 1
    ea = result.enhanced_attacks[0]
    assert ea.baseline_input == "doc attack"
    assert ea.enhanced_input == "doc attack"
    assert ea.techniques == ["doc_technique"]


# ---------------------------------------------------------------------------
# enhance – normal enhancement
# ---------------------------------------------------------------------------

def test_enhance_applies_transformation(monkeypatch):
    enhancer = AttackListEnhancer(simulator_model=None)
    result = enhancer.enhance([_fake_attack("hello")], enhancements=[_passthrough_enhancement()])
    assert len(result.enhanced_attacks) == 1
    assert result.enhanced_attacks[0].enhanced_input == "hello_enhanced"
    assert result.enhanced_attacks[0].error is None


def test_enhance_records_failed_attack_when_transform_raises(monkeypatch):
    monkeypatch.setenv(AttackListEnhancer.RETRY_ATTEMPTS_ENV_VAR, "0")
    enhancer = AttackListEnhancer(simulator_model=None)
    result = enhancer.enhance([_fake_attack("hello")], enhancements=[_failing_enhancement()])
    assert result.failed_attack_count == 1
    assert result.enhanced_attacks[0].is_error is True


def test_enhance_stops_early_when_threshold_exceeded(monkeypatch):
    monkeypatch.setenv(AttackListEnhancer.ERROR_THRESHOLD_ENV_VAR, "0")
    monkeypatch.setenv(AttackListEnhancer.RETRY_ATTEMPTS_ENV_VAR, "0")

    enhancer = AttackListEnhancer(simulator_model=None)
    enhancer._cooldown_with_model_shutdown = lambda cooldown, seconds: None

    result = enhancer.enhance([_fake_attack("x")], enhancements=[_failing_enhancement()])
    assert result.stopped_early is True
    assert len(result.enhanced_attacks) == 1


# ---------------------------------------------------------------------------
# _apply_enhancement retry behavior
# ---------------------------------------------------------------------------

def test_apply_enhancement_retries_and_succeeds(monkeypatch):
    monkeypatch.setenv(AttackListEnhancer.RETRY_ATTEMPTS_ENV_VAR, "1")
    enhancer = AttackListEnhancer(simulator_model=None)
    enhancer._cooldown_with_model_shutdown = lambda cooldown, seconds: None
    calls = {"count": 0}

    def _maybe_fail(prompt, model):
        calls["count"] += 1
        if calls["count"] == 1:
            raise ValueError("first attempt fails")
        return prompt + "_ok"

    enhancement = AttackEnhancement(name="retryable", transform=_maybe_fail, cooldown=lambda s: None)
    output, err = enhancer._apply_enhancement(enhancement, "abc")

    assert err is None
    assert output == "abc_ok"
    assert calls["count"] == 2


def test_apply_enhancement_returns_error_after_retries_exhausted(monkeypatch):
    monkeypatch.setenv(AttackListEnhancer.RETRY_ATTEMPTS_ENV_VAR, "1")
    enhancer = AttackListEnhancer(simulator_model=None)
    enhancer._cooldown_with_model_shutdown = lambda cooldown, seconds: None
    calls = {"count": 0}

    def _always_fail(prompt, model):
        calls["count"] += 1
        raise ValueError("always fails")

    enhancement = AttackEnhancement(name="failing", transform=_always_fail, cooldown=lambda s: None)
    output, err = enhancer._apply_enhancement(enhancement, "abc")

    assert output is None
    assert err is not None
    assert calls["count"] == 2
