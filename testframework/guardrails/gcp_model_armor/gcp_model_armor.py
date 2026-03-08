#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.
import os

from google.api_core.client_options import ClientOptions
from google.cloud.modelarmor_v1 import ModelArmorClient, DataItem, SanitizeUserPromptRequest, \
    SanitizeUserPromptResponse, SanitizeModelResponseRequest, SanitizeModelResponseResponse

from testframework import ChatbotName
from testframework.guardrails.base import BaseGuardrail
from testframework.models import DetectionElement, TestErrorInfo


class GCPModelArmor(BaseGuardrail):
    """Guardrail implementation backed by the GCP Model Armor API.
    Implementation based on https://github.com/meteatamel/genai-beyond-basics/tree/main/samples/guardrails/model_armor
    and https://atamel.dev/posts/2025/08-11_secure_llm_model_armor/
    """

    LOCATION: str = os.environ.get("GCP_MODEL_ARMOR_LOCATION", "europe-west3")
    PROJECT_ID: str = os.environ.get("GCP_MODEL_ARMOR_PROJECT_ID", "N/A")
    TEMPLATE_ID: str = os.environ.get("GCP_MODEL_ARMOR_TEMPLATE_ID", "N/A")

    def __init__(self):
        super().__init__("GCP Model Armor")
        self._client: ModelArmorClient | None = None

    def eval_attack(self, user_prompt: str, attack_description: str, **kwargs) -> DetectionElement:
        prompt_obj: DataItem = DataItem(text=user_prompt)
        request = SanitizeUserPromptRequest(name=self._template_name, user_prompt_data=prompt_obj)
        response: SanitizeUserPromptResponse = self._model_armor_client.sanitize_user_prompt(request=request)

        result = DetectionElement.from_error(TestErrorInfo.from_exception(Exception()))
        return result

    def eval_model_response(self, model_response: str, chatbot: ChatbotName, attack_description: str,
                            **kwargs) -> DetectionElement:
        resp_obj = DataItem(text=model_response)
        request = SanitizeModelResponseRequest(name=self._template_name, model_response_data=resp_obj)
        response: SanitizeModelResponseResponse = self._model_armor_client.sanitize_model_response(request=request)

        result = DetectionElement.from_error(TestErrorInfo.from_exception(Exception()))
        return result

    @property
    def _template_name(self) -> str:
        return f"projects/{self.PROJECT_ID}/locations/{self.LOCATION}/templates/{self.TEMPLATE_ID}"

    @property
    def _model_armor_client(self) -> ModelArmorClient:
        if self._client is None:
            self._client = ModelArmorClient(
                transport="rest",
                client_options=ClientOptions(
                    api_endpoint=f"modelarmor.{self.LOCATION}.rep.googleapis.com"
                ),
            )
        return self._client

# todo: PII ggf. keine Namen und Adressen herausfiltern?
# todo: mehr Prompts im illegalen bereich (csam, weapons, etc.)
