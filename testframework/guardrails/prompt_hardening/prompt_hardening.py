#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.


from __future__ import annotations
from time import perf_counter
from deepteam.test_case import RTTestCase
from testframework.guardrails.base import BaseGuardrail
from testframework import ChatbotName
from testframework.chatbots import ChatbotStore, BaseChatbot
from testframework.guardrails.prompt_hardening.constants import PROMPT_HARDENING_USER_PROMPT, \
    PROMPT_HARDENING_SYSTEM_PROMPT
from testframework.metrics import ToolCallCodeInjectionMetric
from testframework.models import PromptHardeningDetectionElement, RagContext


class PromptHardeningGuardrail(BaseGuardrail):
    """Guardrail that implements prompt hardening via engineered system prompts and simple heuristics."""

    def __init__(self, name: str = "prompt_hardening") -> None:
        super().__init__(name=name)

    def eval_attack(self, user_prompt: str, **kwargs) -> PromptHardeningDetectionElement:
        """ Return an invalid detection element since for PromptHardening one can only evaluate the attack
        in the context of the model response (i.e., whilst generating the response).
        """
        detection = PromptHardeningDetectionElement(
            success=False,
            detected_type=None,
            score=1.0,
            judge_raw_response="Prompt hardening guardrail cannot evaluate the attack without the model response.",
            latency=None,
            scanner_details=[]
        )
        return detection

    def eval_model_response(self, prompt: str, chatbot: ChatbotName, **kwargs) -> PromptHardeningDetectionElement:
        """Re-send the attack but this time with the hardened system prompt."""
        bot: BaseChatbot = ChatbotStore.get_chatbot(chatbot)
        user_prompt = PROMPT_HARDENING_USER_PROMPT.format(user_prompt=prompt)

        file_path = kwargs.get("file_path", None)
        rag_context = kwargs.get("rag_context", None)
        if file_path is None and rag_context is not None:
            user_prompt = self._rebuild_rag_call(rag_context, user_prompt)
        query_started = perf_counter()
        resp = bot.query(user_prompt, is_rag=False, system_prompt=PROMPT_HARDENING_SYSTEM_PROMPT,
                         file_path=file_path)
        query_ended = perf_counter()
        rtt = RTTestCase(vulnerability="", input=prompt, actual_output=resp.response)
        metric = kwargs.get("metric")
        if metric and isinstance(metric, ToolCallCodeInjectionMetric):
            metric.measure(rtt, resp.tool)
        elif metric:
            metric.measure(rtt)
        detection = PromptHardeningDetectionElement(
            success=metric.success,
            detected_type=metric.harm_category if not metric.success else None,
            score=1 - metric.score,
            judge_raw_response=metric.reason,
            latency=query_ended - query_started,
            chatbot_response=resp,
            scanner_details=[]
        )
        return detection

    def _rebuild_rag_call(self, rag_context: RagContext | None, user_prompt: str) -> str:
        """Rebuild the identical rag call that was used in the baseline version of this attack."""
        context_text = "\n\n".join(
            f"[Document {i + 1}]\n{doc}"
            for i, doc in enumerate(rag_context.nodes)
        )
        enhanced_prompt = f"""
Use the given context to answer the question, if needed.
=== CONTEXT ===
{context_text}
=== END CONTEXT ===

{user_prompt}
        """
        return enhanced_prompt
