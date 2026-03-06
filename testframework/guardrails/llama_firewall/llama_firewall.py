#  Copyright (c) 2026.
#  Florian Emanuel Sauer
import json
from testframework import ChatbotName
from testframework.guardrails.base import BaseGuardrail
from testframework.models import DetectionElement, ToolInfo
from llamafirewall import LlamaFirewall as LlamaFirewallGuard, UserMessage, AssistantMessage, Role, ScannerType, Trace


class LlamaFirewall(BaseGuardrail):
    """Guardrail for LlamaFirewall"""

    _firewall: LlamaFirewallGuard | None = None

    _scanners = {
        Role.TOOL: [ScannerType.CODE_SHIELD, ScannerType.PROMPT_GUARD],
        Role.USER: [ScannerType.CODE_SHIELD, ScannerType.PROMPT_GUARD],
        Role.ASSISTANT: [ScannerType.CODE_SHIELD],
    }

    def __init__(self):
        super().__init__("LlamaFirewall")

    @property
    def _llama_firewall(self):
        if self._firewall is None:
            self._firewall = LlamaFirewallGuard(scanners=self._scanners)
        return self._firewall

    def eval_attack(self, user_prompt: str, attack_description: str, **kwargs) -> DetectionElement:
        user_msg = UserMessage(user_prompt)
        res = self._llama_firewall.scan(user_msg)
        pass

    def eval_model_response(self, model_response: str, chatbot: ChatbotName, attack_description: str,
                            **kwargs) -> DetectionElement:
        user_prompt = kwargs.get("prompt", None)
        t_info: ToolInfo = kwargs.get("tool_info", None)
        tool_info = [
            {
                "name": t_info.tool_name,
                "args": json.dumps(t_info.tool_args),
                "was_called": t_info.tool_called,
            }
        ] if t_info is not None else []

        user_msg = UserMessage(user_prompt) if user_prompt is not None else None
        trace: Trace = [user_msg] if user_msg is not None else []
        trace.append(
            AssistantMessage(content=model_response, tool_calls=tool_info)
        )
        res = self._llama_firewall.scan_replay(trace)
        pass
