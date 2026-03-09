#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

import json
import os
from time import perf_counter
from typing import List
import proto
from google.api_core.client_options import ClientOptions
from google.cloud.modelarmor_v1 import (ModelArmorClient, DataItem, SanitizeUserPromptRequest,
                                        SanitizeUserPromptResponse, SanitizeModelResponseRequest,
                                        SanitizeModelResponseResponse, RaiFilterResult,
                                        FilterMatchState, SdpFilterResult, SdpInspectResult, PiAndJailbreakFilterResult,
                                        CsamFilterResult, FilterExecutionState, InvocationResult)
from testframework import ChatbotName, LLMErrorType
from testframework.guardrails.base import BaseGuardrail
from testframework.models import DetectionElement, TestErrorInfo, ScannerDetail


class GcpModelArmor(BaseGuardrail):
    """Guardrail implementation backed by the GCP Model Armor API.
    Implementation based on
        - https://github.com/meteatamel/genai-beyond-basics/tree/main/samples/guardrails/model_armor
        - https://atamel.dev/posts/2025/08-11_secure_llm_model_armor/
        - https://docs.cloud.google.com/python/docs/reference/google-cloud-modelarmor/latest
    """

    LOCATION: str = os.environ.get("GCP_MODEL_ARMOR_LOCATION", "europe-west3")
    PROJECT_ID: str = os.environ.get("GCP_MODEL_ARMOR_PROJECT_ID", "N/A")
    TEMPLATE_ID: str = os.environ.get("GCP_MODEL_ARMOR_TEMPLATE_ID", "N/A")

    def __init__(self):
        super().__init__("GCP Model Armor")
        self._client: ModelArmorClient | None = None

    def eval_attack(self, user_prompt: str, attack_description: str, **kwargs) -> DetectionElement:
        test_started = perf_counter()
        prompt_obj: DataItem = DataItem(text=user_prompt)
        request = SanitizeUserPromptRequest(name=self._template_name, user_prompt_data=prompt_obj)
        response: SanitizeUserPromptResponse = self._model_armor_client.sanitize_user_prompt(request=request)
        test_ended = perf_counter()
        detection = self._build_detection(response, latency=test_ended - test_started)
        return detection

    def eval_model_response(self, model_response: str, chatbot: ChatbotName, attack_description: str,
                            **kwargs) -> DetectionElement:
        t_info = kwargs.get("tool_info", None)
        if t_info:
            name = t_info.tool_name if t_info.tool_name else 'N/A'
            was_called = t_info.tool_called if t_info.tool_called else 'N/A'
            args = t_info.tool_args if t_info.tool_args else 'N/A'
            tool_call = f"Tool Name: {name} \n Tool Was Called: {was_called} \n Tool Call Args: {args}"
        resp_obj = DataItem(text=model_response) if not t_info else DataItem(text=f"=== Tool Call ===\n{tool_call}")
        test_started = perf_counter()
        request = SanitizeModelResponseRequest(name=self._template_name, model_response_data=resp_obj)
        response: SanitizeModelResponseResponse = self._model_armor_client.sanitize_model_response(request=request)
        test_ended = perf_counter()
        detection = self._build_detection(response, latency=test_ended - test_started)
        return detection

    def _build_detection(
            self,
            response: SanitizeUserPromptResponse | SanitizeModelResponseResponse,
            latency: float,
    ) -> DetectionElement:
        sanitization_result = response.sanitization_result
        scanner_details: list[ScannerDetail] = []
        matched_types: list[str] = []
        warning_messages: list[str] = []

        # https://stackoverflow.com/questions/29148391/looping-over-protocol-buffers-attributes-in-python
        # items: filter_name: str | filter_result: attribute rai_filter_result, csam_filter_filter_result, etc.
        for filter_name, filter_result in sanitization_result.filter_results.items():
            # google.cloud.modelarmor_v1.types.service.FilterResult: https://protobuf.dev/reference/python/python-generated/#oneof
            oneof_field_that_currently_has_values = filter_result._pb.WhichOneof("filter_result")
            if not oneof_field_that_currently_has_values:
                continue
            scanner_detail, matched_labels, warnings = self._scanner_detail_from_filter(
                filter_name=filter_name,
                filter_result=getattr(filter_result, oneof_field_that_currently_has_values),
            )
            scanner_details.append(scanner_detail)
            matched_types.extend(matched_labels)
            warning_messages.extend(warnings)

        attack_found = sanitization_result.filter_match_state == FilterMatchState.MATCH_FOUND
        success = not attack_found
        score = 1.0 if attack_found else 0.0

        detected_type = ", ".join(matched_types) if matched_types else "Not details on matched types available."

        invocation_result = sanitization_result.invocation_result
        if invocation_result in (InvocationResult.PARTIAL, InvocationResult.FAILURE,
                                 InvocationResult.INVOCATION_RESULT_UNSPECIFIED):
            warning_messages.append(
                f"Invocation result: {invocation_result.name}"
            )

        if warning_messages:
            error = TestErrorInfo(LLMErrorType.UNKNOWN, " | ".join(warning_messages))
        else:
            error = None

        return DetectionElement(
            success=success,
            detected_type=detected_type,
            score=score,
            judge_raw_response=json.dumps(proto.Message.to_dict(response), ensure_ascii=True, default=str),
            latency=latency,
            scanner_details=scanner_details,
            error=error,
        )

    def _scanner_detail_from_filter(self, filter_name: str, filter_result) -> tuple[ScannerDetail, List, List]:
        warnings: List = []
        match_was_found = False
        subtypes_of_found_match: List = []
        execution_state = None
        sanitized_input = ""
        matched_labels = []

        if isinstance(filter_result, RaiFilterResult):
            execution_state = filter_result.execution_state
            match_was_found = filter_result.match_state == FilterMatchState.MATCH_FOUND
            for rai_type, rai_result in filter_result.rai_filter_type_results.items():
                if rai_result.match_state == FilterMatchState.MATCH_FOUND:
                    subtypes_of_found_match.append(f"rai:{rai_type}")

        elif isinstance(filter_result, SdpFilterResult):
            nested_name = filter_result._pb.WhichOneof("result")  # noqa
            if nested_name:
                nested = getattr(filter_result, nested_name)
                execution_state = getattr(nested, "execution_state", None)
                match_was_found = getattr(nested, "match_state", None) == FilterMatchState.MATCH_FOUND
                if isinstance(nested, SdpInspectResult):
                    for finding in nested.findings:
                        if finding.info_type:
                            subtypes_of_found_match.append(f"sdp:{finding.info_type}")
                # SdpDeidentifyResult is not activated for this example; it won't be handled
            else:
                warnings.append(f"{filter_name}: no SDP result was returned")

        elif isinstance(filter_result, PiAndJailbreakFilterResult):
            execution_state = filter_result.execution_state
            match_was_found = filter_result.match_state == FilterMatchState.MATCH_FOUND
            if match_was_found:
                subtypes_of_found_match.append(
                    f"pi_and_jailbreak:{filter_result.confidence_level.name}"
                )

        elif isinstance(filter_result, CsamFilterResult):
            execution_state = filter_result.execution_state
            match_was_found = filter_result.match_state == FilterMatchState.MATCH_FOUND

        else:
            # todo: handle fallback for unknown cases
            pass

        if execution_state == FilterExecutionState.EXECUTION_SKIPPED:
            warnings.append(f"{filter_name}: execution was skipped")

        reason_parts = [
            "Match found" if match_was_found else "No match found",
        ]
        if execution_state is not None:
            reason_parts.append(
                f"Execution: {execution_state.name}"
            )

        if match_was_found:
            matched_labels = [filter_name]
            matched_labels.extend(subtypes_of_found_match)

        scanner_detail = ScannerDetail(
            name=filter_name,
            score=1.0 if match_was_found else 0.0,
            reason=" | ".join(reason_parts),
            is_valid=not match_was_found,
            sanitized_input=sanitized_input,
        )
        return scanner_detail, matched_labels, warnings

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
