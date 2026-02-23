from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List
from uuid import UUID, uuid4

from .enums import Category, LLM


@dataclass
class TimestampRange:
    start: datetime
    end: datetime


@dataclass
class RagNode:
    text: str


@dataclass
class RagContext:
    embedding_vector: float | None = None
    embedding_model: str | None = None
    nodes: List[RagNode] = field(default_factory=list)


@dataclass
class PromptVariants:
    baseline: str
    attack: str
    enhanced: str


@dataclass
class PromptTokens:
    baseline: int
    attack: int
    enhanced: int


@dataclass
class LlmParamsPerModel:
    temperature: float | None = None
    # extendable for more params


@dataclass
class LlmParams:
    gpt_41: LlmParamsPerModel | None = None
    gpt_5: LlmParamsPerModel | None = None


@dataclass
class ToolInfo:
    tool_called: bool
    tool_call_params: str | None = None


@dataclass
class ModelResponse:
    response: str
    token_count: int
    tool: ToolInfo | None = None


@dataclass
class LlmResponsePerModel:
    response: str
    token: int
    attack_success: bool
    tool: ToolInfo


@dataclass
class LlmResponses:
    gpt_41: LlmResponsePerModel | None = None
    gpt_5: LlmResponsePerModel | None = None


@dataclass
class DetectionResult:
    success: bool
    detected_type: Category | None
    severity: float
    judge_raw_response: str
    timestamp: TimestampRange


@dataclass
class PromptHardeningPerModel:
    input_detection: DetectionResult
    output_detection: DetectionResult


@dataclass
class PromptHardening:
    gpt_41: PromptHardeningPerModel | None = None
    gpt_5: PromptHardeningPerModel | None = None


@dataclass
class LlmGuard:
    # Placeholder for future LLM guard integrations
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Protection:
    prompt_hardening: PromptHardening
    llm_guard: LlmGuard | None = None


@dataclass
class AttackMetadata:
    severity: str | None = None
    category_raw: str | None = None
    tool_check: str | None = None
    tool_check_condition: str | None = None
    remote_attack_generation: str | None = None
    document: str | None = None


@dataclass
class Attack:
    attack_id: UUID
    subcategory: str
    prompt: PromptVariants
    prompt_tokens: PromptTokens
    rag_context: RagContext
    llm_params: LlmParams
    llm_responses: LlmResponses
    protection: Protection
    metadata: AttackMetadata | None = None


@dataclass
class TestCaseResult:
    """Container for the result of a single test case for one attack."""

    attack: Attack


@dataclass
class AttackCategoryResult:
    category_id: UUID
    name: Category
    attacks: Dict[str, Attack] = field(default_factory=dict)


@dataclass
class TestRunTimestamp:
    start: datetime
    end: datetime


@dataclass
class TestRunResult:
    run_id: UUID
    timestamp: TestRunTimestamp
    attack_categories: List[AttackCategoryResult]

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

