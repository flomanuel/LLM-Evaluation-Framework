from enum import Enum
from typing import Dict, List, cast
from deepteam.vulnerabilities import BaseVulnerability, PromptLeakage  # type: ignore
from deepteam.vulnerabilities.prompt_leakage import PromptLeakageType  # type: ignore
from deepteam.metrics import BaseRedTeamingMetric, HarmMetric  # type: ignore
from deepeval.models import DeepEvalBaseLLM
from deepteam.test_case import RTTestCase

from testframework.testcases.system_prompt_leakage.subcategory import SystemPromptLeakageSubcategory
from testframework.util.csv_loader import CSVLoader


class SystemPromptLeakageAttacks(BaseVulnerability):
    """Class that builds system prompt leakage attack prompts from CSV and DeepTeam."""

    def __init__(
            self,
            types: List[Enum] = None,
            simulator_model: DeepEvalBaseLLM | None = None,
            evaluation_model: DeepEvalBaseLLM | None = None,
            async_mode: bool = True,
            verbose_mode: bool = True,
    ):
        self.types = types if types else [SystemPromptLeakageSubcategory.INSTRUCTIONS,
                                          SystemPromptLeakageSubcategory.GUARD_EXPOSURE]
        self.async_mode = async_mode
        self.verbose_mode = verbose_mode
        self.simulator_model = simulator_model
        self.evaluation_model = evaluation_model
        self.default_attack_builder: BaseVulnerability | None = None
        super().__init__(types)

    def subcategory_to_prompt_leakage_type(self, subcategory) -> str | None:
        """Map SystemPromptLeakageSubcategory to DeepTeam PromptLeakageType value."""
        mapping: Dict[SystemPromptLeakageSubcategory, str] = {
            SystemPromptLeakageSubcategory.INSTRUCTIONS: PromptLeakageType.INSTRUCTIONS.value,
            SystemPromptLeakageSubcategory.GUARD_EXPOSURE: PromptLeakageType.GUARD_EXPOSURE.value,
        }
        return mapping.get(subcategory)

    def simulate_attacks(self, purpose: str = None) -> List[RTTestCase]:
        attacks: List[RTTestCase] = []
        attacks.extend(
            RTTestCase(
                vulnerability=self.get_name(),
                input=prompt)
            for prompt, _ in CSVLoader.load_prompts_from_csv(
                file_path="2_schaedlich_manuell_erstellt_basic.csv",
                categories=["system-prompt-leakage"]
            )
        )

        deep_team_types: List[str] = []
        for subcategory in self.types:
            mapped_type = self.subcategory_to_prompt_leakage_type(subcategory)
            if mapped_type:
                deep_team_types.append(mapped_type)

        if deep_team_types:
            self.default_attack_builder = PromptLeakage(
                simulator_model=self.simulator_model,
                evaluation_model=self.evaluation_model,
                types=deep_team_types
            )
            attacks.extend(self.default_attack_builder.simulate_attacks())

        return attacks

    def _get_metric(self, attack: RTTestCase) -> BaseRedTeamingMetric:
        if self.default_attack_builder:
            attack_type = cast(PromptLeakageType, attack.vulnerability_type)
            return cast(PromptLeakage, self.default_attack_builder)._get_metric(type=attack_type)
        return HarmMetric(harm_category="system-prompt-leakage", model=self.evaluation_model)

    def get_name(self) -> str:
        return "SystemPromptLeakage"
