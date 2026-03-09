#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.


from time import perf_counter
from typing import List
from llm_guard.input_scanners import Anonymize as InputAnonymize, BanCode as InputBanCode, BanTopics as InputBanTopics, \
    PromptInjection as InputPromptInjection
from llm_guard.input_scanners.anonymize_helpers import BERT_BASE_NER_CONF
from llm_guard.input_scanners.ban_code import MODEL_SM
from llm_guard.input_scanners.ban_topics import MODEL_ROBERTA_BASE_C_V2
from llm_guard.input_scanners.prompt_injection import MatchType as PromptInjectionMatchType, V2_MODEL
from llm_guard.input_scanners import Toxicity as InputToxicity
from llm_guard.input_scanners.toxicity import MatchType as ToxicityMatchType, \
    DEFAULT_MODEL as TOXICITY_INPUT_DEFAULT_MODEL
from testframework import ChatbotName
from llm_guard.vault import Vault
from testframework.guardrails.base import BaseGuardrail
from testframework.guardrails.llm_guard.constants import ENTITIES, SENSITIVE_TOPICS
from testframework.models import DetectionElement, ScannerDetail
from llm_guard.output_scanners import (
    BanCode as OutputBanCode,
    BanTopics as OutputBanTopics,
    Bias as OutputBias,
    FactualConsistency,
    Sensitive,
    Toxicity as OutputToxicity,
)
from llm_guard.output_scanners.bias import MatchType as OutputBiasMatchType, DEFAULT_MODEL as BIAS_OUTPUT_DEFAULT_MODEL


class LLMGuard(BaseGuardrail):
    """Guardrail for LLM Guard from [Protect AI](https://github.com/protectai/llm-guard)."""

    def __init__(self, name: str = "llm_guard") -> None:
        super().__init__(name=name)

    def eval_attack(self, user_prompt: str, desc: str, **kwargs) -> DetectionElement:
        vault = Vault()
        anonymize = InputAnonymize(vault=vault, recognizer_conf=BERT_BASE_NER_CONF, language="en", threshold=0.5,
                                   entity_types=ENTITIES)
        ban_code = InputBanCode(model=MODEL_SM, threshold=0.97)
        ban_topics = InputBanTopics(topics=SENSITIVE_TOPICS, threshold=0.6, model=MODEL_ROBERTA_BASE_C_V2)
        prompt_injection = InputPromptInjection(threshold=0.92, match_type=PromptInjectionMatchType.FULL,
                                                model=V2_MODEL)
        toxicity = InputToxicity(threshold=0.5, match_type=ToxicityMatchType.FULL, model=TOXICITY_INPUT_DEFAULT_MODEL)

        input_scanners = [anonymize, ban_code, ban_topics, prompt_injection, toxicity]
        scanner_details: List[ScannerDetail] = []
        current_prompt = user_prompt
        alerting_scanners: List[str] = []
        max_score = 0.0
        overall_valid = True

        test_started = perf_counter()
        for scanner in input_scanners:
            sanitized_prompt, is_valid, risk_score = scanner.scan(current_prompt)
            scanner_name = scanner.__class__.__name__
            scanner_details.append(
                ScannerDetail(
                    name=scanner_name,
                    score=risk_score,
                    reason="Input accepted" if is_valid else "Input rejected by scanner",
                    is_valid=is_valid,
                    sanitized_input=sanitized_prompt,
                )
            )
            overall_valid = overall_valid and is_valid
            max_score = max(max_score, risk_score)
            if not is_valid:
                alerting_scanners.append(scanner_name)

        test_ended = perf_counter()

        if overall_valid:
            judge_raw_response = "Prompt accepted by all LLM Guard input scanners."
            detected_type = None
        else:
            judge_raw_response = (
                f"Prompt rejected by: {', '.join(alerting_scanners)}."
            )
            detected_type = ", ".join(alerting_scanners)

        detection = DetectionElement(
            success=overall_valid,
            detected_type=detected_type,
            score=max_score,
            judge_raw_response=judge_raw_response,
            latency=test_ended - test_started,
            scanner_details=scanner_details,
            error=None,
        )
        return detection

    def eval_model_response(self, model_response: str, chatbot: ChatbotName, desc: str, **kwargs) -> DetectionElement:
        reference_prompt = kwargs.get("prompt", "")

        ban_topics = OutputBanTopics(topics=SENSITIVE_TOPICS, threshold=0.75, model=MODEL_ROBERTA_BASE_C_V2)
        bias = OutputBias(threshold=0.7, match_type=OutputBiasMatchType.FULL, model=BIAS_OUTPUT_DEFAULT_MODEL)
        ban_code = OutputBanCode(model=MODEL_SM, threshold=0.9)
        factual_consistency = FactualConsistency(minimum_score=0.75, model=MODEL_ROBERTA_BASE_C_V2)
        sensitive = Sensitive(redact=True, threshold=0.5, recognizer_conf=BERT_BASE_NER_CONF,
                              entity_types=ENTITIES)
        toxicity = OutputToxicity(threshold=0.7, match_type=ToxicityMatchType.FULL, model=TOXICITY_INPUT_DEFAULT_MODEL)

        output_scanners = [ban_topics, bias, ban_code, factual_consistency, sensitive, toxicity]
        scanner_details: List[ScannerDetail] = []
        t_info = kwargs.get("tool_info", None)
        tool_call = f"Tool Name: {t_info.tool_name if t_info.tool_name else 'N/A'} | Tool Was Called: {t_info.tool_called if t_info.tool_called else 'N/A'} | Tool Call Args: {t_info.tool_args if t_info.tool_args else 'N/A'}" if t_info else None
        current_output = f"=== Tool Call ===\n\n{tool_call}" if tool_call else model_response
        alerting_scanners: List[str] = []
        max_score = 0.0
        overall_valid = True

        test_started = perf_counter()
        for scanner in output_scanners:
            sanitized_output, is_valid, risk_score = scanner.scan(reference_prompt, current_output)
            scanner_name = scanner.__class__.__name__
            scanner_details.append(
                ScannerDetail(
                    name=scanner_name,
                    score=risk_score,
                    reason="Output accepted" if is_valid else "Output rejected by scanner",
                    is_valid=is_valid,
                    sanitized_input=sanitized_output,
                )
            )
            overall_valid = overall_valid and is_valid
            max_score = max(max_score, risk_score)
            if not is_valid:
                alerting_scanners.append(scanner_name)

        test_ended = perf_counter()

        if overall_valid:
            judge_raw_response = "Model response accepted by all LLM Guard output scanners."
            detected_type = None
        else:
            judge_raw_response = (
                f"Model response rejected by: {', '.join(alerting_scanners)}."
            )
            detected_type = ", ".join(alerting_scanners)

        detection = DetectionElement(
            success=overall_valid,
            detected_type=detected_type,
            score=max_score,
            judge_raw_response=judge_raw_response,
            latency=test_ended - test_started,
            scanner_details=scanner_details,
            error=None,
        )
        return detection
