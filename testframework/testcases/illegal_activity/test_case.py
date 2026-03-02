#  Copyright (c) 2026.
#  Florian Emanuel Sauer

from __future__ import annotations

import os
import shlex
import time
from typing import List, cast

from deepeval.models import OllamaModel
from deepteam.metrics import BaseRedTeamingMetric
from deepteam.test_case import RTTestCase
from testframework.enums import Category
from testframework.testcases.base import BaseTestCase
from testframework.testcases.illegal_activity.builder import IllegalActivity
from testframework.testcases.illegal_activity.subcategory import IllegalActivitySubcategory


class IllegalActivityTestCase(BaseTestCase):
    """Test case using DeepTeam's IllegalActivity vulnerability as an attack source."""

    OLLAMA_INFERENCE_REQUEST_TIMEOUT = 300

    def __init__(self, subcategories: List[IllegalActivitySubcategory]) -> None:
        super().__init__(
            Category.ILLEGAL_ACTIVITY,
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

        self.attack_builder = IllegalActivity(self.subcategories, self.simulator_model, self.evaluation_model)

    def _get_metric(self, attack: RTTestCase) -> BaseRedTeamingMetric:
        return self.attack_builder._get_metric(attack)

    def simulate_attacks(self, attacks_per_vulnerability_type: int = 1) -> List[RTTestCase]:
        return cast(IllegalActivity, self.attack_builder).simulate_attacks(
            attacks_per_vulnerability_type=attacks_per_vulnerability_type
        )
