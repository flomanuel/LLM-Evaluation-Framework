#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.


from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List
from uuid import uuid4

from deepteam.test_case import RTTestCase

from testframework.enums import Category, ChatbotName, Severity


class LLMErrorType(str, Enum):
    """Types of test execution errors."""
    TIMEOUT = "TIMEOUT"
    CONNECTION_ERROR = "CONNECTION_ERROR"
    GENERATION_ERROR = "GENERATION_ERROR"
    THRESHOLD_EXCEEDED = "THRESHOLD_EXCEEDED"
    UNKNOWN = "UNKNOWN"


@dataclass
class TestErrorInfo:
    """Information about an LLM call error."""
    error_type: LLMErrorType
    message: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def from_exception(cls, exc: Exception) -> "TestErrorInfo":
        """Create an LLMErrorInfo from an exception."""
        exc_module = type(exc).__module__

        if "deepeval" in exc_module or "deepteam" in exc_module or "openai" in exc_module:
            return cls(LLMErrorType.GENERATION_ERROR, str(exc))

        if isinstance(exc, TimeoutError):
            return cls(LLMErrorType.TIMEOUT, str(exc))
        if isinstance(exc, ConnectionError):
            return cls(LLMErrorType.CONNECTION_ERROR, str(exc))

        return cls(LLMErrorType.UNKNOWN, str(exc))


@dataclass
class TimestampRange:
    """Timestamp range for the tests."""
    start: datetime
    end: datetime


@dataclass
class RagContext:
    """Context for RAG retrieval."""
    embedding_model: str | None
    nodes: List[str]


@dataclass
class DocumentContext:
    """Context for document retrieval."""
    document: str


@dataclass
class PromptVariants:
    """prmopt variants before and after enhancement."""
    baseline: str
    enhanced: str


@dataclass
class ToolInfo:
    """Information about a tool call."""
    tool_called: bool
    tool_name: str | None = None
    tool_args: dict[str, Any] | str | None = None


@dataclass
class ChatbotResponse:
    """Response from a chatbot."""
    prompt: str
    raw_prompt: str
    response: str
    system_prompt: str
    tool: ToolInfo
    prompt_tokens: int  # including the RAG context
    response_tokens: int
    rag_context: RagContext | None
    document_content: DocumentContext | None
    file_path: str | None = None
    error: TestErrorInfo | None = None

    @property
    def is_error(self) -> bool:
        """Check if this response represents an error."""
        return self.error is not None

    @classmethod
    def from_error(
            cls,
            error: TestErrorInfo,
            system_prompt: str = "",
            prompt: str = "",
    ) -> "ChatbotResponse":
        """Create an error ChatbotResponse."""
        return cls(
            prompt=prompt,
            raw_prompt="",
            response="",
            system_prompt=system_prompt,
            tool=ToolInfo(tool_called=False),
            prompt_tokens=-1,
            response_tokens=-1,
            rag_context=None,
            document_content=None,
            error=error,
        )


@dataclass
class ChatbotResponseEvaluation:
    """Evaluation result of a chatbot response."""
    chatbot_response: ChatbotResponse
    score: float
    reason: str
    success: bool
    metric: str
    error: TestErrorInfo | None = None

    @property
    def is_error(self) -> bool:
        """Check if this evaluation or its response has an error."""
        return self.error is not None or self.chatbot_response.is_error

    @classmethod
    def from_error(cls, chatbot_response: ChatbotResponse,
                   error: TestErrorInfo | None = None) -> "ChatbotResponseEvaluation":
        """Create an error ChatbotResponseEvaluation."""
        return cls(
            chatbot_response=chatbot_response,
            score=-1.0,
            reason="Evaluation failed due to error",
            error=error or chatbot_response.error,
            success=False,
            metric="",
        )


@dataclass
class ScannerDetail:
    """Detailed information about a guardrail's scanner result."""
    name: str
    score: float
    reason: str
    is_valid: bool | None
    sanitized_input: str


@dataclass
class DetectionElement:
    """Container for a detection result of a guardrail."""
    success: bool
    detected_type: Category | str | None
    score: float
    judge_raw_response: str
    latency: float | None
    scanner_details: List[ScannerDetail]
    error: TestErrorInfo | None = None

    @property
    def is_error(self) -> bool:
        """Check if this detection represents an error."""
        return self.error is not None

    @classmethod
    def from_error(cls, error: TestErrorInfo) -> "DetectionElement":
        """Create an error DetectionElement."""
        return cls(
            success=False,
            detected_type=None,
            score=0.0,
            judge_raw_response="",
            latency=None,
            scanner_details=[],
            error=error,
        )


@dataclass
class PromptHardeningDetectionElement(DetectionElement):
    """Detection element for prompt hardening."""
    chatbot_response: ChatbotResponse | None = None


@dataclass
class DetectionResult:
    """Container for the detection results of a guardrail for a specific chatbot."""
    input_detection: DetectionElement
    output_detection: DetectionElement


@dataclass
class EnhancedAttack:
    """Container for a base attack and its enhanced representation."""
    attack_case: RTTestCase
    baseline_input: str
    enhanced_input: str
    techniques: List[str] = field(default_factory=list)
    error: TestErrorInfo | None = None

    @property
    def is_error(self) -> bool:
        """Check if the enhancement for this attack failed."""
        return self.error is not None


@dataclass
class AttackEnhancementResult:
    """Summary of all enhanced attacks."""
    enhanced_attacks: List[EnhancedAttack]
    planned_attack_count: int
    failed_attack_count: int
    error_threshold_percent: float
    stopped_early: bool = False

    @property
    def invalid_percentage(self) -> float:
        """Return the percentage of failed enhancements out of all planned enhancements."""
        if self.planned_attack_count <= 0:
            return 0.0
        return (self.failed_attack_count / self.planned_attack_count) * 100.0

    @property
    def threshold_exceeded(self) -> bool:
        """Check if the failed enhancement rate is strictly above the configured threshold."""
        return (
                self.planned_attack_count > 0
                and self.invalid_percentage > self.error_threshold_percent
        )


@dataclass
class Attack:
    """One LLM-specific attack"""
    category: str
    subcategory: Enum | None
    techniques: List[str]
    severity: Severity
    prompt: PromptVariants
    llm_responses: Dict[ChatbotName, ChatbotResponseEvaluation]
    protection: Dict[str, Dict[ChatbotName, DetectionResult]]
    error: TestErrorInfo | None = None

    @property
    def is_error(self) -> bool:
        """Check if this attack has a generation error or any response errors."""
        if self.error is not None:
            return True
        return any(evaluation.is_error for evaluation in self.llm_responses.values())

    @classmethod
    def from_generation_error(
            cls,
            category: str,
            subcategories: List[Enum] | None,
            severity: Severity,
            error: TestErrorInfo,
    ) -> "Attack":
        """Create an Attack representing a generation failure."""
        return cls(
            category=category,
            subcategory=subcategories if subcategories else [],
            severity=severity,
            prompt=PromptVariants(baseline="", enhanced=""),
            llm_responses={},
            protection={},
            techniques=[],
            error=error,
        )

    @classmethod
    def from_enhancement_error(
            cls,
            category: str,
            subcategories: List[Enum] | None,
            severity: Severity,
            baseline_input: str,
            enhanced_input: str,
            techniques: List[str],
            error: TestErrorInfo,
    ) -> "Attack":
        """Create an Attack representing a failed prompt enhancement."""
        return cls(
            category=category,
            subcategory=subcategories if subcategories else [],
            severity=severity,
            prompt=PromptVariants(baseline=baseline_input, enhanced=enhanced_input),
            llm_responses={},
            protection={},
            techniques=techniques,
            error=error,
        )


@dataclass
class TestCaseResult:
    @dataclass
    class ModelInfo:
        """Model used for generating the attacks and techniques."""
        attack_and_vulnerability_generation: str | None = None

    category: Category
    subcategories: List[str]
    model: ModelInfo = field(default_factory=ModelInfo)
    attacks: Dict[str, Attack] = field(default_factory=dict)
    generation_error: TestErrorInfo | None = None
    enhancement_error: TestErrorInfo | None = None

    @property
    def identifier(self) -> str:
        """Return identifier in format 'category_subcategory' or 'category'."""
        if self.subcategories:
            return f"{self.category.value}_{";".join(self.subcategories)}"
        return self.category.value

    @property
    def has_errors(self) -> bool:
        """Check if this test case has any errors."""
        if self.generation_error is not None:
            return True
        if self.enhancement_error is not None:
            return True
        return any(attack.is_error for attack in self.attacks.values())

    @property
    def error_count(self) -> int:
        """Count the number of attacks with errors."""
        count = 1 if self.generation_error else 0
        count += 1 if self.enhancement_error else 0
        count += sum(1 for attack in self.attacks.values() if attack.is_error)
        return count


@dataclass
class TestRunTimestamp:
    """Timestamps for the whole test run."""
    start: datetime
    end: datetime


@dataclass
class TestRunResult:
    """Result of a test run."""
    run_id: str
    timestamp: TestRunTimestamp
    attack_categories: List[TestCaseResult]

    def to_json_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def new_empty(cls) -> "TestRunResult":
        now = datetime.now(timezone.utc)
        return cls(
            run_id=str(uuid4()),
            timestamp=TestRunTimestamp(start=now, end=now),
            attack_categories=[],
        )
