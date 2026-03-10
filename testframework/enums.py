#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.


from enum import Enum


class Category(str, Enum):
    """Main attack/test categories."""
    BENIGN = "benign"
    ILLEGAL_ACTIVITY = "illegal-activity"
    ETHICS = "ethics"
    FAIRNESS = "fairness"
    SYSTEM_PROMPT_LEAKAGE = "system-prompt-leakage"
    SENSITIVE_INFORMATION_DISCLOSURE = "sensitive-information-disclosure"
    EXCESSIVE_AGENCY = "excessive-agency"
    INDIRECT_PROMPT_INJECTION = "indirect-prompt-injection"
    PRIVACY_VIOLATIONS = "privacy-violations"
    DATA_AND_MODEL_EXTRACTION = "data-and-model-extraction"
    BIAS = "bias"
    TOXICITY = "toxicity"
    COMPETITION = "competition"
    ROBUSTNESS = "robustness"
    INDIRECT_INSTRUCTION = "indirect-instruction"


class ChatbotName(str, Enum):
    """Supported LLM models / Chatbots."""
    LANGCHAIN_GPT_41 = "LANGCHAIN_GPT_41"
    LANGCHAIN_GPT_5 = "LANGCHAIN_GPT_5"
    OPENAI = "OPENAI"
    DUMMY = "DUMMY"
    LANGCHAIN = "LANGCHAIN"


class Severity(str, Enum):
    """Define whether a test case (i.e. a prompt / attack) is harmful."""
    UNSAFE = "unsafe"
    SAFE = "safe"
