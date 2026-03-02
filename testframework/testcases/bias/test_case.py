#  Copyright (c) 2026.
#  Florian Emanuel Sauer

from __future__ import annotations

import os
import shlex
import time
from typing import cast, List

from deepeval.models import OllamaModel
from deepteam.metrics import BaseRedTeamingMetric
from deepteam.test_case import RTTestCase
from deepteam.vulnerabilities.bias import BiasType
from testframework.enums import Category
from testframework.testcases.base import BaseTestCase
from testframework.testcases.bias.builder import BiasAttacks
from testframework.testcases.bias.subcategory import BiasSubcategory


class BiasTestCase(BaseTestCase):
    """Test case for bias attacks."""

    OLLAMA_INFERENCE_REQUEST_TIMEOUT = 300

    def __init__(self, subcategories: List[BiasSubcategory]) -> None:
        super().__init__(
            Category.BIAS,
            subcategories,
        )

        model_id = os.environ.get("LOCAL_MODEL_ID", False)
        if model_id is not False:
            self.simulator_model = OllamaModel(
                model=model_id,
                # https://huggingface.co/mlabonne/gemma-3-27b-it-abliterated-GGUF
                generation_kwargs={"top_p": 0.95, "top_k": 64},
                temperature=1.0,
                timeout=self.OLLAMA_INFERENCE_REQUEST_TIMEOUT,
            )
            running_models = os.popen("ollama ps").read().strip().splitlines()
            if len(running_models) <= 1:
                safe_model_id = shlex.quote(model_id)
                os.system(f"ollama run {safe_model_id} >/dev/null 2>&1 &")
                time.sleep(10)

        self.attack_builder = BiasAttacks(self.subcategories, self.simulator_model, self.evaluation_model)

    def _get_metric(self, attack: RTTestCase) -> BaseRedTeamingMetric:
        attack_type = cast(BiasType, attack.vulnerability_type)
        return cast(BiasAttacks, self.attack_builder)._get_metric(type=attack_type)  # pylint: disable=protected-access

    def simulate_attacks(self, attacks_per_vulnerability_type: int = 1) -> List[RTTestCase]:
        return cast(BiasAttacks, self.attack_builder).simulate_attacks(
            attacks_per_vulnerability_type=attacks_per_vulnerability_type
        )
