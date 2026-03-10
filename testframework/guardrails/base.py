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
        raise NotImplementedError

    @abstractmethod
    def eval_model_response(self, model_response: str, chatbot: ChatbotName, **kwargs) -> DetectionElement:
        raise NotImplementedError

    @staticmethod
    def _build_evidence_text(evidence: Any, tool_info: ToolInfo | None) -> str:
        if tool_info is not None:
            return BaseGuardrail._tool_trace_to_text(tool_info)

        if evidence is None:
            return "none"

        if isinstance(evidence, str):
            return evidence

        try:
            return json.dumps(evidence, ensure_ascii=True, default=str)
        except TypeError:
            return str(evidence)

    @staticmethod
    def _tool_trace_to_text(tool_info: ToolInfo) -> str:
        if not tool_info.tool_called:
            return "No tool call was made."
        return (
            f"Tool called: {tool_info.tool_name or 'unknown'}; "
            f"Arguments: {tool_info.tool_args if tool_info.tool_args is not None else 'none'}"
        )
