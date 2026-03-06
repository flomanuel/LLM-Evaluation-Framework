#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.



from __future__ import annotations
from pathlib import Path
from typing import List
from loguru import logger
from testframework import ChatbotName
from testframework.chatbots import LangChainChatbot, VectorStore
from testframework.chatbots.store import ChatbotStore
from testframework.testcases import BenignTestCase, BiasTestCase, CompetitionTestCase, EthicsTestCase, \
    ExcessiveAgencyTestCase, FairnessTestCase, IllegalActivityTestCase, IndirectInstructionTestCase, \
    PrivacyViolationsTestCase, RobustnessTestCase, SystemPromptLeakageTestCase, ToxicityTestCase, FairnessSubcategory
from testframework.testcases.base import BaseTestCase
from testframework.testcases.benign.subcategory import BenignSubcategory
from testframework.testcases.bias.subcategory import BiasSubcategory
from testframework.testcases.ethics.subcategory import EthicsSubcategory
from testframework.testcases.illegal_activity.subcategory import IllegalActivitySubcategory
from testframework.testcases.indirect_instruction.subcategory import IndirectInstructionSubcategory
from testframework.testcases.toxicity.subcategory import ToxicitySubcategory
from testframework.tests.base_test import Test


class DefaultTest(Test):
    """Concrete Test implementation that runs all test cases defined in this module."""

    def __init__(self, results_dir: Path | None = None) -> None:
        super().__init__(name="baseline", results_dir=results_dir)

    def setup_chatbots(self) -> None:
        logger.debug("Setting up baseline chatbots")
        vector_store = VectorStore()
        # todo: enable both chatbots again
        # gpt_5 = LangChainChatbot(
        #     name=ChatbotName.LANGCHAIN_GPT_5,
        #     model="gpt-5",
        #     vector_store=vector_store)
        # ChatbotStore.add_chatbot(gpt_5)
        gpt_41 = LangChainChatbot(
            name=ChatbotName.LANGCHAIN_GPT_41,
            model="gpt-4.1",
            vector_store=vector_store)
        ChatbotStore.add_chatbot(gpt_41)
        logger.debug("Baseline chatbot setup complete")

    def get_test_cases(self) -> List[BaseTestCase]:
        ethics = [EthicsSubcategory.BANKING, EthicsSubcategory.HARM_PREVENTION, EthicsSubcategory.MORAL_INTEGRITY]
        ind_inst = [IndirectInstructionSubcategory.DOCUMENT_EMBEDDED_INSTRUCTIONS]
        return [
            BenignTestCase(),
            # FairnessTestCase(),
            # EthicsTestCase(ethics),
            # SystemPromptLeakageTestCase(),
            # ExcessiveAgencyTestCase(),
            # IndirectInstructionTestCase(ind_inst),
            # # todo: PrivacyViolations prüfen, ob die zugehörigen Einträge aus der CSV-Datei richtig ausgewertet und im JSON kategorisiert werden!
            # PrivacyViolationsTestCase(),
            # BiasTestCase([BiasSubcategory.RACE]),
            # BiasTestCase([BiasSubcategory.GENDER]),
            # BiasTestCase([BiasSubcategory.RELIGION]),
            # BiasTestCase([BiasSubcategory.POLITICS]),
            # IllegalActivityTestCase([IllegalActivitySubcategory.WEAPONS]),
            # IllegalActivityTestCase([IllegalActivitySubcategory.ILLEGAL_DRUGS]),
            # IllegalActivityTestCase([IllegalActivitySubcategory.VIOLENT_CRIME]),
            # IllegalActivityTestCase([IllegalActivitySubcategory.NONVIOLENT_CRIME]),
            # IllegalActivityTestCase([IllegalActivitySubcategory.SEX_CRIME]),
            # IllegalActivityTestCase([IllegalActivitySubcategory.CYBERCRIME]),
            # IllegalActivityTestCase([IllegalActivitySubcategory.CHILD_EXPLOITATION]),
            # ToxicityTestCase([ToxicitySubcategory.INSULTS]),
            # ToxicityTestCase([ToxicitySubcategory.PROFANITY]),
            # ToxicityTestCase([ToxicitySubcategory.THREATS]),
            # ToxicityTestCase([ToxicitySubcategory.MOCKERY]),
        ]
