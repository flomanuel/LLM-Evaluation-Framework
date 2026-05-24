#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

from testframework.redteam.builders.deepeval_attack_builders import TemplateDrivenAttackBuilder
from testframework.testcases.illegal_activity.builder import IllegalActivity
from testframework.testcases.illegal_activity.subcategory import IllegalActivitySubcategory
from testframework.util.csv_loader import CSVLoader


class _FakeRow:
    def __init__(self, prompt: str):
        self.prompt = prompt

    def build_attack_metadata(self):
        return {}


def test_template_builder_empty_types_defaults_to_all_template_keys():
    builder = TemplateDrivenAttackBuilder(
        vulnerability="Example",
        prompts_by_type={
            "a": ["prompt-a"],
            "b": ["prompt-b"],
        },
        types=[],
    )

    attacks = builder.simulate_attacks(attacks_per_vulnerability_type=1)

    assert len(attacks) == 2
    assert {attack.vulnerability_type for attack in attacks} == {"a", "b"}


def test_illegal_activity_crime_subcategory_loads_default_and_specific_categories(monkeypatch):
    captured_categories: list[list[str]] = []

    def _fake_loader(*args, **kwargs):
        captured_categories.append(kwargs["categories"])
        return []

    monkeypatch.setattr(CSVLoader, "load_prompts_from_csv", staticmethod(_fake_loader))

    builder = IllegalActivity(types=[IllegalActivitySubcategory.SEX_CRIME])
    attacks = builder.simulate_attacks(attacks_per_vulnerability_type=1)

    assert captured_categories == [["illegal-activity_crime"], ["illegal-activity_sex-crime"]]
    assert len(attacks) == 1
    assert attacks[0].vulnerability_type == IllegalActivitySubcategory.SEX_CRIME


def test_illegal_activity_always_adds_default_crime_rows_as_violent(monkeypatch):
    captured_categories: list[list[str]] = []

    def _fake_loader(*args, **kwargs):
        categories = kwargs["categories"]
        captured_categories.append(categories)
        if categories == ["illegal-activity_crime"]:
            return [_FakeRow("crime-row")]
        if categories == ["illegal-activity_weapons"]:
            return [_FakeRow("weapons-row")]
        return []

    monkeypatch.setattr(CSVLoader, "load_prompts_from_csv", staticmethod(_fake_loader))

    builder = IllegalActivity(types=[IllegalActivitySubcategory.WEAPONS])
    attacks = builder.simulate_attacks(attacks_per_vulnerability_type=1)

    assert captured_categories == [["illegal-activity_crime"], ["illegal-activity_weapons"]]
    assert len(attacks) == 2
    assert attacks[0].vulnerability_type == IllegalActivitySubcategory.VIOLENT_CRIME
    assert attacks[1].vulnerability_type == IllegalActivitySubcategory.WEAPONS
