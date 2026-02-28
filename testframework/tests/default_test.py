#  Copyright (c) 2026.
#  Florian Emanuel Sauer

from __future__ import annotations
from pathlib import Path
from typing import List
from loguru import logger
from testframework import ChatbotName
from testframework.chatbots import LangChainChatbot, VectorStore, DummyChatbot
from testframework.chatbots.store import ChatbotStore
from testframework.testcases import BenignTestCase, BiasTestCase, CompetitionTestCase, EthicsTestCase, \
    ExcessiveAgencyTestCase, FairnessTestCase, IllegalActivityTestCase, IndirectInstructionTestCase, \
    PrivacyViolationsTestCase, RobustnessTestCase, SystemPromptLeakageTestCase, ToxicityTestCase
from testframework.testcases.base import BaseTestCase
from testframework.testcases.ethics.subcategory import EthicsSubcategory
from testframework.testcases.fairness.subcategory import FairnessSubcategory
from testframework.testcases.illegal_activity.subcategory import IllegalActivitySubcategory
from testframework.testcases.indirect_instruction.subcategory import IndirectInstructionSubcategory
from testframework.tests.base_test import Test


class DefaultTest(Test):
    """Concrete Test implementation that runs all test cases defined in this module."""

    def __init__(self, results_dir: Path | None = None) -> None:
        super().__init__(name="baseline", results_dir=results_dir)

    def setup_chatbots(self) -> None:
        logger.debug("Setting up baseline chatbots")
        vector_store = VectorStore()
        gpt_5 = LangChainChatbot(
            name=ChatbotName.LANGCHAIN_GPT_5,
            model="gpt-5",
            vector_store=vector_store)
        ChatbotStore.add_chatbot(gpt_5)
        gpt_41 = LangChainChatbot(
            name=ChatbotName.LANGCHAIN_GPT_41,
            model="gpt-4.1",
            vector_store=vector_store)
        ChatbotStore.add_chatbot(gpt_41)
        logger.debug("Baseline chatbot setup complete")

    def get_test_cases(self) -> List[BaseTestCase]:
        illegal_activity = [
            IllegalActivitySubcategory.WEAPONS,
            IllegalActivitySubcategory.ILLEGAL_DRUGS,
            IllegalActivitySubcategory.VIOLENT_CRIME,
            IllegalActivitySubcategory.NONVIOLENT_CRIME,
            IllegalActivitySubcategory.SEX_CRIME,
            IllegalActivitySubcategory.CYBERCRIME,
            IllegalActivitySubcategory.CHILD_EXPLOITATION,
        ]
        ethics = [EthicsSubcategory.BANKING, EthicsSubcategory.HARM_PREVENTION, EthicsSubcategory.MORAL_INTEGRITY]
        indirect_instruction = [IndirectInstructionSubcategory.DOCUMENT_EMBEDDED_INSTRUCTIONS]
        return [
            #BenignTestCase(),
            #IllegalActivityTestCase(illegal_activity),
            #EthicsTestCase(ethics),
            #FairnessTestCase(),
            #SystemPromptLeakageTestCase(),
            #ExcessiveAgencyTestCase(),
            #IndirectInstructionTestCase(indirect_instruction),
            #PrivacyViolationsTestCase(),
            #BiasTestCase(),
            #ToxicityTestCase(),
            #CompetitionTestCase(),
            #RobustnessTestCase(),
        ]
