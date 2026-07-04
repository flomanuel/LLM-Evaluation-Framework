#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

from __future__ import annotations

from pydantic import BaseModel, Field

from testframework.enums import ChatbotName
from testframework.persistence.entity.detection import (
    DetectionElementEntity,
    DetectionResultEntity,
    ScannerDetailEntity,
)
from testframework.persistence.entity.enums import DetectionStage


class ScannerDetailInputModel(BaseModel):
    """Input model for a single scanner's output within a detection element."""

    name: str = Field(min_length=1)
    score: float = Field(ge=0.0, le=1.0)
    reason: str
    sanitized_input: str = ""
    is_valid: bool | None = None

    def to_entity(self) -> ScannerDetailEntity:
        return ScannerDetailEntity(
            detection_element_id=0,  # FK set by caller
            name=self.name,
            score=self.score,
            reason=self.reason,
            sanitized_input=self.sanitized_input,
            is_valid=self.is_valid,
        )


class DetectionElementInputModel(BaseModel):
    """Input model for one detection stage (input or output) result."""

    stage: DetectionStage
    success: bool
    score: float = Field(ge=0.0, le=1.0)
    judge_raw_response: str
    detected_type: str | None = None
    chatbot_response_id: int | None = None
    scanner_details: list[ScannerDetailInputModel] = Field(default_factory=list)

    def to_entity(self) -> DetectionElementEntity:
        entity = DetectionElementEntity(
            detection_result_id=0,  # FK set by caller
            stage=self.stage,
            success=self.success,
            score=self.score,
            judge_raw_response=self.judge_raw_response,
            detected_type=self.detected_type,
            chatbot_response_id=self.chatbot_response_id,
        )
        entity.scanner_details = [sd.to_entity() for sd in self.scanner_details]
        return entity


class DetectionResultInputModel(BaseModel):
    """Input model for a full guardrail evaluation (input + output detection) on one chatbot."""

    guardrail_name: str = Field(min_length=1)
    chatbot_name: ChatbotName
    input_detection: DetectionElementInputModel
    output_detection: DetectionElementInputModel

    def to_entity(self) -> DetectionResultEntity:
        entity = DetectionResultEntity(
            attack_id=0,  # FK set by caller
            guardrail_name=self.guardrail_name,
            chatbot_name=self.chatbot_name,
        )
        input_el = self.input_detection.to_entity()
        output_el = self.output_detection.to_entity()
        entity.detection_elements = [input_el, output_el]
        return entity
