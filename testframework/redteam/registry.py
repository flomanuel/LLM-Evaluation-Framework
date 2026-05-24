#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

"""Central registry for internal red-team builders and metric strategies."""

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any

from deepeval.models import DeepEvalBaseLLM

from testframework.redteam.builders.deepeval_attack_builders import (
    CompetitionAttackBuilder,
    RobustnessAttackBuilder,
)
from testframework.redteam.metric_adapters import HarmMetric
from testframework.redteam.metric_protocol import RedTeamingMetric


BuilderFactory = Callable[..., Any]
MetricFactory = Callable[..., RedTeamingMetric]


@dataclass(frozen=True)
class RedTeamCategoryConfig:
    """Registry configuration for one category."""

    builder_factory: BuilderFactory
    metric_factory: MetricFactory


CATEGORY_REGISTRY: dict[str, RedTeamCategoryConfig] = {
    "competition": RedTeamCategoryConfig(
        builder_factory=CompetitionAttackBuilder,
        metric_factory=lambda evaluation_model, attack=None: HarmMetric(
            harm_category="Competition and market manipulation",
            model=evaluation_model,
        ),
    ),
    "robustness": RedTeamCategoryConfig(
        builder_factory=RobustnessAttackBuilder,
        metric_factory=lambda evaluation_model, attack=None: HarmMetric(
            harm_category="Prompt hijacking and robustness failures",
            model=evaluation_model,
        ),
    ),
}


def create_builder(
        category: str,
        subcategories: list[Enum] | None,
        simulator_model: DeepEvalBaseLLM | None | str,
        evaluation_model: DeepEvalBaseLLM | None | str,
) -> Any:
    """Create the configured builder for a category."""
    config = CATEGORY_REGISTRY[category]
    return config.builder_factory(
        types=subcategories,
        simulator_model=simulator_model,
        evaluation_model=evaluation_model,
    )


def create_metric(
        category: str,
        evaluation_model: DeepEvalBaseLLM | None | str,
        attack: Any = None,
) -> RedTeamingMetric:
    """Create the configured metric for a category."""
    config = CATEGORY_REGISTRY[category]
    return config.metric_factory(evaluation_model, attack=attack)
