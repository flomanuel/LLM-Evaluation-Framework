#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.


from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any
from testframework import ChatbotName
from testframework.models import DetectionElement, ToolInfo


class BaseGuardrail(ABC):
    """Abstract base for guardrails."""

    name: str

    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    def eval_attack(self, user_prompt: str, **kwargs) -> DetectionElement:
        """Evaluate the attack."""
        raise NotImplementedError

    @abstractmethod
    def eval_model_response(self, model_response: str, chatbot: ChatbotName, **kwargs) -> DetectionElement:
        """Evaluate the response from the attacked model."""
        raise NotImplementedError
