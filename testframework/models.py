from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List
from uuid import uuid4
from testframework.enums import Category, ChatbotName, TestCaseName, Severity


class LLMErrorType(str, Enum):
    """Types of LLM-related errors."""
    TIMEOUT = "TIMEOUT"
    CONNECTION_ERROR = "CONNECTION_ERROR"
    GENERATION_ERROR = "GENERATION_ERROR"
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
    start: datetime
    end: datetime


@dataclass
class RagContext:
    embedding_vector: float | None = None
    embedding_model: str | None = None
    nodes: List[str] = field(default_factory=list)


@dataclass
class PromptVariants:
    baseline: str
    enhanced: str


@dataclass
class ModelConfig:
    temperature: float | None = None
    top_p: float | None = None
    top_k: int | None = None
    max_tokens: int | None = None


@dataclass
class ToolInfo:
    tool_called: bool
    tool_call_params: str | None = None


@dataclass
class ChatbotResponse:
    response: str
    system_prompt: str
    tool: ToolInfo
    llm_params: ModelConfig
    prompt_tokens: int  # including the RAG context
    response_tokens: int
    rag_context: RagContext | None
    file_path: str | None = None
    error: TestErrorInfo | None = None

    @property
    def is_error(self) -> bool:
        """Check if this response represents an error."""
        return self.error is not None

    @classmethod
    def from_error(cls, error: TestErrorInfo, system_prompt: str = "") -> "ChatbotResponse":
        """Create an error ChatbotResponse."""
        return cls(
            response="",
            system_prompt=system_prompt,
            tool=ToolInfo(tool_called=False),
            llm_params=ModelConfig(),
            prompt_tokens=-1,
            response_tokens=-1,
            rag_context=None,
            error=error,
        )


@dataclass
class ChatbotResponseEvaluation:
    chatbot_response: ChatbotResponse
    score: float
    reason: str
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
        )


@dataclass
class DetectionElement:
    success: bool
    detected_type: Category | None
    severity: float
    judge_raw_response: str
    timestamp: TimestampRange
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
            severity=0.0,
            judge_raw_response="",
            timestamp=TimestampRange(start=error.timestamp, end=error.timestamp),
            error=error,
        )


@dataclass
class DetectionResult:
    input_detection: DetectionElement
    output_detection: DetectionElement


@dataclass
class Attack:
    category: str
    subcategory: str | None
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
            subcategory: str | None,
            severity: Severity,
            error: TestErrorInfo,
    ) -> "Attack":
        """Create an Attack representing a generation failure."""
        return cls(
            category=category,
            subcategory=subcategory,
            severity=severity,
            prompt=PromptVariants(baseline="", enhanced=""),
            llm_responses={},
            protection={},
            error=error,
        )


@dataclass
class TestCaseResult:
    name: TestCaseName
    category: Category
    attacks: Dict[str, Attack] = field(default_factory=dict)
    generation_error: TestErrorInfo | None = None

    @property
    def has_errors(self) -> bool:
        """Check if this test case has any errors."""
        if self.generation_error is not None:
            return True
        return any(attack.is_error for attack in self.attacks.values())

    @property
    def error_count(self) -> int:
        """Count the number of attacks with errors."""
        count = 1 if self.generation_error else 0
        count += sum(1 for attack in self.attacks.values() if attack.is_error)
        return count


@dataclass
class TestRunTimestamp:
    start: datetime
    end: datetime


@dataclass
class TestRunResult:
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
