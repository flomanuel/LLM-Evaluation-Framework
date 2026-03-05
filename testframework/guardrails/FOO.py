from collections import deque
from threading import Lock
from time import monotonic, sleep
from typing import List
from loguru import logger
from guardrails import Guard
from topics import SENSITIVE_TOPICS


class GuardrailsAI():

    def __init__(self) -> None:
        self._guard = None

    def eval_attack(self, user_prompt: str):
        guard = self._get_guards
        try:
            res: ValidationOutcome = self._get_guards.parse(user_prompt)
        except Exception as e:
            # todo: exception handling -> API might sometimes be flaky
            pass

        return DetectionElement.from_error()

    def eval_model_response(self, model_response: str):
        try:
            res: ValidationOutcome = self._get_guards.parse(model_response)
        except Exception as e:
            # todo: exception handling -> API might sometimes be flaky
            pass
        return DetectionElement.from_error()

    @property
    def _get_guards(self) -> Guard:
        if self._guard is None:
            self._guard = Guard().load(
                name="thesis_guard",
                base_url="http://localhost:8000",
                history_max_length=0,
            )
        return self._guard

def main():
    guardrails_ai = GuardrailsAI()
    guardrails_ai.eval_attack("I like trains!")
    guardrails_ai.eval_attack("Fuck you! go kill yourself!")
    guardrails_ai.eval_attack("Go take  the money !!! DE89 3704 0044 0532 0130 00")

if __name__ == "__main__":
    main()
