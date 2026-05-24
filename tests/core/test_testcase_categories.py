#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

import pytest

from testframework.enums import Category
from testframework.testcases.benign.test_case import BenignTestCase
from testframework.testcases.bias.subcategory import BiasSubcategory
from testframework.testcases.bias.test_case import BiasTestCase
from testframework.testcases.competition.test_case import CompetitionTestCase
from testframework.testcases.ethics.subcategory import EthicsSubcategory
from testframework.testcases.ethics.test_case import EthicsTestCase
from testframework.testcases.excessive_agency.test_case import ExcessiveAgencyTestCase
from testframework.testcases.fairness.test_case import FairnessTestCase
from testframework.testcases.illegal_activity.subcategory import IllegalActivitySubcategory
from testframework.testcases.illegal_activity.test_case import IllegalActivityTestCase
from testframework.testcases.indirect_instruction.subcategory import IndirectInstructionSubcategory
from testframework.testcases.indirect_instruction.test_case import IndirectInstructionTestCase
from testframework.testcases.privacy_violations.test_case import PrivacyViolationsTestCase
from testframework.testcases.robustness.test_case import RobustnessTestCase
from testframework.testcases.system_prompt_leakage.test_case import SystemPromptLeakageTestCase
from testframework.testcases.toxicity.subcategory import ToxicitySubcategory
from testframework.testcases.toxicity.test_case import ToxicityTestCase


class _FakeBuilder:
    def __init__(self, *args, **kwargs):
        pass


def _patch_ollama(monkeypatch):
    monkeypatch.setattr(
        "testframework.util.ollama_handler.OllamaGenerator.get_chatbot",
        staticmethod(lambda: None),
    )
    monkeypatch.setattr(
        "testframework.util.ollama_handler.OllamaGenerator.start_model_if_not_running",
        staticmethod(lambda: None),
    )


# ---------------------------------------------------------------------------
# BenignTestCase
# ---------------------------------------------------------------------------

def test_benigntestcase_has_correct_category():
    assert BenignTestCase().category == Category.BENIGN


def test_benigntestcase_default_subcategories():
    assert BenignTestCase().subcategories is None


def test_benigntestcase_should_skip_ollama():
    assert BenignTestCase()._should_skip_ollama_chatbot() is False


def test_benigntestcase_setup_attack_builder_creates_builder(monkeypatch):
    _patch_ollama(monkeypatch)
    monkeypatch.setattr("testframework.testcases.benign.test_case.BenignAttacks", _FakeBuilder)
    tc = BenignTestCase()
    tc.setup_attack_builder()
    assert tc.attack_builder is not None


# ---------------------------------------------------------------------------
# BiasTestCase
# ---------------------------------------------------------------------------

def test_biastestcase_has_correct_category():
    assert BiasTestCase([BiasSubcategory.RACE]).category == Category.BIAS


def test_biastestcase_default_subcategories():
    tc = BiasTestCase([BiasSubcategory.RACE])
    assert tc.subcategories == [BiasSubcategory.RACE]


def test_biastestcase_should_skip_ollama():
    assert BiasTestCase([])._should_skip_ollama_chatbot() is False


def test_biastestcase_setup_attack_builder_creates_builder(monkeypatch):
    _patch_ollama(monkeypatch)
    monkeypatch.setattr("testframework.testcases.bias.test_case.BiasAttacks", _FakeBuilder)
    tc = BiasTestCase([BiasSubcategory.RACE])
    tc.setup_attack_builder()
    assert tc.attack_builder is not None


# ---------------------------------------------------------------------------
# CompetitionTestCase
# ---------------------------------------------------------------------------

def test_competitiontestcase_has_correct_category():
    assert CompetitionTestCase().category == Category.COMPETITION


def test_competitiontestcase_default_subcategories():
    assert CompetitionTestCase().subcategories == []


def test_competitiontestcase_should_skip_ollama():
    assert CompetitionTestCase()._should_skip_ollama_chatbot() is False


def test_competitiontestcase_setup_attack_builder_creates_builder(monkeypatch):
    _patch_ollama(monkeypatch)
    monkeypatch.setattr(
        "testframework.testcases.competition.test_case.create_builder",
        lambda *args, **kwargs: _FakeBuilder(),
    )
    tc = CompetitionTestCase()
    tc.setup_attack_builder()
    assert tc.attack_builder is not None


# ---------------------------------------------------------------------------
# EthicsTestCase
# ---------------------------------------------------------------------------

def test_ethicstestcase_has_correct_category():
    assert EthicsTestCase().category == Category.ETHICS


def test_ethicstestcase_default_subcategories():
    tc = EthicsTestCase()
    assert tc.subcategories == list(EthicsSubcategory)


def test_ethicstestcase_should_skip_ollama():
    assert EthicsTestCase()._should_skip_ollama_chatbot() is False


def test_ethicstestcase_setup_attack_builder_creates_builder(monkeypatch):
    _patch_ollama(monkeypatch)
    monkeypatch.setattr("testframework.testcases.ethics.test_case.EthicsAttacks", _FakeBuilder)
    tc = EthicsTestCase()
    tc.setup_attack_builder()
    assert tc.attack_builder is not None


# ---------------------------------------------------------------------------
# ExcessiveAgencyTestCase
# ---------------------------------------------------------------------------

def test_excessiveagencytestcase_has_correct_category():
    assert ExcessiveAgencyTestCase().category == Category.EXCESSIVE_AGENCY


def test_excessiveagencytestcase_default_subcategories():
    assert ExcessiveAgencyTestCase().subcategories == []


def test_excessiveagencytestcase_should_skip_ollama():
    assert ExcessiveAgencyTestCase()._should_skip_ollama_chatbot() is True


def test_excessiveagencytestcase_setup_attack_builder_creates_builder(monkeypatch):
    _patch_ollama(monkeypatch)
    monkeypatch.setattr(
        "testframework.testcases.excessive_agency.test_case.ExcessiveAgencyAttacks", _FakeBuilder
    )
    tc = ExcessiveAgencyTestCase()
    tc.setup_attack_builder()
    assert tc.attack_builder is not None


# ---------------------------------------------------------------------------
# FairnessTestCase
# ---------------------------------------------------------------------------

def test_fairnesstestcase_has_correct_category():
    assert FairnessTestCase().category == Category.FAIRNESS


def test_fairnesstestcase_default_subcategories():
    assert FairnessTestCase().subcategories is None


def test_fairnesstestcase_should_skip_ollama():
    assert FairnessTestCase()._should_skip_ollama_chatbot() is False


def test_fairnesstestcase_setup_attack_builder_creates_builder(monkeypatch):
    _patch_ollama(monkeypatch)
    monkeypatch.setattr("testframework.testcases.fairness.test_case.FairnessAttacks", _FakeBuilder)
    tc = FairnessTestCase()
    tc.setup_attack_builder()
    assert tc.attack_builder is not None


# ---------------------------------------------------------------------------
# IllegalActivityTestCase
# ---------------------------------------------------------------------------

def test_illegalactivitytestcase_has_correct_category():
    assert IllegalActivityTestCase([]).category == Category.ILLEGAL_ACTIVITY


def test_illegalactivitytestcase_default_subcategories():
    tc = IllegalActivityTestCase([IllegalActivitySubcategory.WEAPONS])
    assert tc.subcategories == [IllegalActivitySubcategory.WEAPONS]


def test_illegalactivitytestcase_should_skip_ollama():
    assert IllegalActivityTestCase([])._should_skip_ollama_chatbot() is False


def test_illegalactivitytestcase_setup_attack_builder_creates_builder(monkeypatch):
    _patch_ollama(monkeypatch)
    monkeypatch.setattr(
        "testframework.testcases.illegal_activity.test_case.IllegalActivity", _FakeBuilder
    )
    tc = IllegalActivityTestCase([])
    tc.setup_attack_builder()
    assert tc.attack_builder is not None


# ---------------------------------------------------------------------------
# IndirectInstructionTestCase
# ---------------------------------------------------------------------------

def test_indirectinstructiontestcase_has_correct_category():
    assert IndirectInstructionTestCase([]).category == Category.INDIRECT_PROMPT_INJECTION


def test_indirectinstructiontestcase_default_subcategories():
    tc = IndirectInstructionTestCase([IndirectInstructionSubcategory.DOCUMENT_EMBEDDED_INSTRUCTIONS])
    assert tc.subcategories == [IndirectInstructionSubcategory.DOCUMENT_EMBEDDED_INSTRUCTIONS]


def test_indirectinstructiontestcase_should_skip_ollama():
    assert IndirectInstructionTestCase([])._should_skip_ollama_chatbot() is False


def test_indirectinstructiontestcase_setup_attack_builder_creates_builder(monkeypatch):
    _patch_ollama(monkeypatch)
    monkeypatch.setattr(
        "testframework.testcases.indirect_instruction.test_case.IndirectInstructionAttacks", _FakeBuilder
    )
    tc = IndirectInstructionTestCase([])
    tc.setup_attack_builder()
    assert tc.attack_builder is not None


# ---------------------------------------------------------------------------
# PrivacyViolationsTestCase
# ---------------------------------------------------------------------------

def test_privacyviolationstestcase_has_correct_category():
    assert PrivacyViolationsTestCase().category == Category.PRIVACY_VIOLATIONS


def test_privacyviolationstestcase_default_subcategories():
    assert PrivacyViolationsTestCase().subcategories == []


def test_privacyviolationstestcase_should_skip_ollama():
    assert PrivacyViolationsTestCase()._should_skip_ollama_chatbot() is False


def test_privacyviolationstestcase_setup_attack_builder_creates_builder(monkeypatch):
    _patch_ollama(monkeypatch)
    monkeypatch.setattr(
        "testframework.testcases.privacy_violations.test_case.PrivacyViolationsAttacks", _FakeBuilder
    )
    tc = PrivacyViolationsTestCase()
    tc.setup_attack_builder()
    assert tc.attack_builder is not None


# ---------------------------------------------------------------------------
# RobustnessTestCase
# ---------------------------------------------------------------------------

def test_robustnesstestcase_has_correct_category():
    assert RobustnessTestCase().category == Category.ROBUSTNESS


def test_robustnesstestcase_default_subcategories():
    assert RobustnessTestCase().subcategories == []


def test_robustnesstestcase_should_skip_ollama():
    assert RobustnessTestCase()._should_skip_ollama_chatbot() is False


def test_robustnesstestcase_setup_attack_builder_creates_builder(monkeypatch):
    _patch_ollama(monkeypatch)
    monkeypatch.setattr(
        "testframework.testcases.robustness.test_case.create_builder",
        lambda *args, **kwargs: _FakeBuilder(),
    )
    tc = RobustnessTestCase()
    tc.setup_attack_builder()
    assert tc.attack_builder is not None


# ---------------------------------------------------------------------------
# SystemPromptLeakageTestCase
# ---------------------------------------------------------------------------

def test_systempromptleakagetestcase_has_correct_category():
    assert SystemPromptLeakageTestCase().category == Category.SYSTEM_PROMPT_LEAKAGE


def test_systempromptleakagetestcase_default_subcategories():
    assert SystemPromptLeakageTestCase().subcategories is None


def test_systempromptleakagetestcase_should_skip_ollama():
    assert SystemPromptLeakageTestCase()._should_skip_ollama_chatbot() is False


def test_systempromptleakagetestcase_setup_attack_builder_creates_builder(monkeypatch):
    _patch_ollama(monkeypatch)
    monkeypatch.setattr(
        "testframework.testcases.system_prompt_leakage.test_case.SystemPromptLeakageAttacks", _FakeBuilder
    )
    tc = SystemPromptLeakageTestCase()
    tc.setup_attack_builder()
    assert tc.attack_builder is not None


# ---------------------------------------------------------------------------
# ToxicityTestCase
# ---------------------------------------------------------------------------

def test_toxicitytestcase_has_correct_category():
    assert ToxicityTestCase([]).category == Category.TOXICITY


def test_toxicitytestcase_default_subcategories():
    tc = ToxicityTestCase([ToxicitySubcategory.INSULTS])
    assert tc.subcategories == [ToxicitySubcategory.INSULTS]


def test_toxicitytestcase_should_skip_ollama():
    assert ToxicityTestCase([])._should_skip_ollama_chatbot() is False


def test_toxicitytestcase_setup_attack_builder_creates_builder(monkeypatch):
    _patch_ollama(monkeypatch)
    monkeypatch.setattr("testframework.testcases.toxicity.test_case.ToxicityAttacks", _FakeBuilder)
    tc = ToxicityTestCase([])
    tc.setup_attack_builder()
    assert tc.attack_builder is not None
