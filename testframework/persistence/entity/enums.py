#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

from enum import Enum

import sqlalchemy as sa

from testframework.enums import Category, ChatbotName, Severity
from testframework.models import LLMErrorType


class DetectionStage(str, Enum):
    INPUT = "input"
    OUTPUT = "output"


CategoryType = sa.Enum(
    Category,
    name="category",
    values_callable=lambda e: [m.value for m in e],
)

SeverityType = sa.Enum(
    Severity,
    name="severity",
    values_callable=lambda e: [m.value for m in e],
)

ChatbotNameType = sa.Enum(
    ChatbotName,
    name="chatbot_name",
    values_callable=lambda e: [m.value for m in e],
)

LLMErrorTypeType = sa.Enum(
    LLMErrorType,
    name="llm_error_type",
    values_callable=lambda e: [m.value for m in e],
)

DetectionStageType = sa.Enum(
    DetectionStage,
    name="detection_stage",
    values_callable=lambda e: [m.value for m in e],
)
