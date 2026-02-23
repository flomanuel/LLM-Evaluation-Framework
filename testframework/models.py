from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List
from uuid import UUID, uuid4

from .enums import Category, Chatbot, TestCaseName, Severity


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


@dataclass
class ToolInfo:
    tool_called: bool
    tool_call_params: str | None = None


@dataclass
class ChatbotResponse:
    response: str
    system_prompt: str
    tool: ToolInfo
    rag_context: RagContext
    file_path: str
    llm_params: ModelConfig
    prompt_tokens: int  # including the RAG context
    response_tokens: int


@dataclass
class ChatbotResponseEvaluation:
    chatbot_response: ChatbotResponse
    score: float
    reason: str


@dataclass
class DetectionElement:
    success: bool
    detected_type: Category | None
    severity: float
    judge_raw_response: str
    timestamp: TimestampRange


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
    llm_responses: Dict[Chatbot, ChatbotResponseEvaluation]
    protection: Dict[str, Dict[Chatbot, DetectionResult]]


@dataclass
class TestCaseResult:
    name: TestCaseName
    category: Category
    attacks: Dict[UUID, Attack] = field(default_factory=dict)


@dataclass
class TestRunTimestamp:
    start: datetime
    end: datetime


@dataclass
class TestRunResult:
    run_id: UUID
    timestamp: TestRunTimestamp
    attack_categories: Dict[str, TestCaseResult]

    def to_json_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def new_empty(cls) -> "TestRunResult":
        now = datetime.utcnow()
        return cls(
            run_id=uuid4(),
            timestamp=TestRunTimestamp(start=now, end=now),
            attack_categories=[],
        )
