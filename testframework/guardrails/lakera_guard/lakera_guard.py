#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.
from testframework import ChatbotName
from testframework.guardrails.base import BaseGuardrail
from testframework.models import DetectionElement


class LakeraGuard(BaseGuardrail):

    def __init__(self):
        super().__init__("Lakera Guard")

    def eval_attack(self, user_prompt: str, attack_description: str, **kwargs) -> DetectionElement:
        pass

    def eval_model_response(self, model_response: str, chatbot: ChatbotName, attack_description: str,
                            **kwargs) -> DetectionElement:
        pass

