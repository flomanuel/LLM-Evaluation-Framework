#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

"""DTO ↔ entity conversions — single source of truth used by service and importer."""

from datetime import datetime, timezone

from testframework.enums import Category, ChatbotName, Severity
from testframework.models import (
    Attack,
    AttackEnhancementResult,
    ChatbotResponse,
    ChatbotResponseEvaluation,
    DetectionElement,
    DetectionResult,
    EnhancedAttack,
    LLMErrorType,
    PromptHardeningDetectionElement,
    PromptVariants,
    RagContext,
    DocumentContext,
    ScannerDetail,
    TestCaseResult,
    TestErrorInfo,
    TestRunResult,
    TestRunTimestamp,
    ToolInfo,
)
from testframework.persistence.entity.analysis import AnalysisRunEntity, SummaryErrorEntity, SummaryRowEntity
from testframework.persistence.entity.attack import AttackEntity
from testframework.persistence.entity.chatbot_response import (
    ChatbotResponseEntity,
    ChatbotResponseEvaluationEntity,
)
from testframework.persistence.entity.detection import (
    DetectionElementEntity,
    DetectionResultEntity,
    ScannerDetailEntity,
)
from testframework.persistence.entity.test_case import TestCaseEntity
from testframework.persistence.entity.test_run import TestRunEntity

_PROMPT_HARDENING = "prompt_hardening"


# ---------------------------------------------------------------------------
# DTO → Entity
# ---------------------------------------------------------------------------


def _error_columns(error: TestErrorInfo | None) -> dict:
    """Return the three embedded error column values for a given TestErrorInfo."""
    if error is None:
        return {"error_type": None, "error_message": None, "error_timestamp": None}
    return {
        "error_type": error.error_type.value,
        "error_message": error.message,
        "error_timestamp": error.timestamp,
    }


def scanner_detail_to_entity(sd: ScannerDetail) -> ScannerDetailEntity:
    return ScannerDetailEntity(
        detection_element_id=0,
        name=sd.name,
        score=sd.score,
        reason=sd.reason,
        sanitized_input=sd.sanitized_input,
        is_valid=sd.is_valid,
    )


def detection_element_to_entity(
    de: DetectionElement,
    stage: str,
    chatbot_response_entity: ChatbotResponseEntity | None = None,
) -> DetectionElementEntity:
    err = _error_columns(de.error)
    detected_type_str: str | None = None
    if de.detected_type is not None:
        detected_type_str = (
            de.detected_type.value if isinstance(de.detected_type, Category) else str(de.detected_type)
        )

    entity = DetectionElementEntity(
        detection_result_id=0,
        stage=stage,
        success=de.success,
        score=de.score,
        judge_raw_response=de.judge_raw_response,
        detected_type=detected_type_str,
        latency=de.latency,
        error_type=err["error_type"],
        error_message=err["error_message"],
        error_timestamp=err["error_timestamp"],
        chatbot_response_id=None,
    )
    entity.scanner_details = [scanner_detail_to_entity(s) for s in de.scanner_details]
    if chatbot_response_entity is not None:
        entity.chatbot_response_id = chatbot_response_entity.id
    return entity


def chatbot_response_to_entity(
    resp: ChatbotResponse,
    evaluation_id: int = 0,
) -> ChatbotResponseEntity:
    err = _error_columns(resp.error)
    tool_args_value = None
    if resp.tool.tool_args is not None:
        if isinstance(resp.tool.tool_args, dict):
            tool_args_value = resp.tool.tool_args
        else:
            tool_args_value = str(resp.tool.tool_args)

    return ChatbotResponseEntity(
        evaluation_id=evaluation_id,
        prompt=resp.prompt,
        raw_prompt=resp.raw_prompt,
        response=resp.response,
        system_prompt=resp.system_prompt,
        prompt_tokens=resp.prompt_tokens,
        response_tokens=resp.response_tokens,
        tool_called=resp.tool.tool_called,
        tool_name=resp.tool.tool_name,
        tool_args=tool_args_value,
        rag_embedding_model=resp.rag_context.embedding_model if resp.rag_context else None,
        rag_nodes=resp.rag_context.nodes if resp.rag_context else None,
        document_content=resp.document_content.document if resp.document_content else None,
        file_path=resp.file_path,
        error_type=err["error_type"],
        error_message=err["error_message"],
        error_timestamp=err["error_timestamp"],
    )


def evaluation_to_entity(
    chatbot_name: ChatbotName,
    evaluation: ChatbotResponseEvaluation,
    attack_id: int = 0,
) -> ChatbotResponseEvaluationEntity:
    err = _error_columns(evaluation.error)
    entity = ChatbotResponseEvaluationEntity(
        attack_id=attack_id,
        chatbot_name=chatbot_name.value,
        score=evaluation.score,
        reason=evaluation.reason,
        success=evaluation.success,
        metric=evaluation.metric,
        error_type=err["error_type"],
        error_message=err["error_message"],
        error_timestamp=err["error_timestamp"],
    )
    entity.chatbot_response = chatbot_response_to_entity(evaluation.chatbot_response)
    return entity


def detection_result_to_entities(
    guardrail_name: str,
    chatbot_name: ChatbotName,
    detection_result: DetectionResult,
    attack_id: int = 0,
    chatbot_response_entity: ChatbotResponseEntity | None = None,
) -> DetectionResultEntity:
    entity = DetectionResultEntity(
        attack_id=attack_id,
        guardrail_name=guardrail_name,
        chatbot_name=chatbot_name.value,
    )
    if guardrail_name == _PROMPT_HARDENING:
        output_de = detection_result.output_detection
        assert isinstance(output_de, PromptHardeningDetectionElement)
        resp_entity: ChatbotResponseEntity | None = None
        if output_de.chatbot_response is not None:
            resp_entity = chatbot_response_to_entity(output_de.chatbot_response)
        output_el = detection_element_to_entity(output_de, "output")
        output_el.prompt_hardening_chatbot_response = resp_entity
        entity.detection_elements = [
            detection_element_to_entity(detection_result.input_detection, "input"),
            output_el,
        ]
    else:
        entity.detection_elements = [
            detection_element_to_entity(detection_result.input_detection, "input"),
            detection_element_to_entity(detection_result.output_detection, "output"),
        ]
    return entity


def attack_to_entity(
    attack_id_key: str,
    attack: Attack,
    test_case_id: int = 0,
) -> AttackEntity:
    err = _error_columns(attack.error)
    subcategory_str: str | None = None
    if attack.subcategory is not None:
        if hasattr(attack.subcategory, "value"):
            subcategory_str = str(attack.subcategory.value)
        else:
            subcategory_str = str(attack.subcategory)

    entity = AttackEntity(
        test_case_id=test_case_id,
        category=attack.category if isinstance(attack.category, str) else attack.category.value,
        severity=attack.severity.value,
        prompt_baseline=attack.prompt.baseline,
        prompt_enhanced=attack.prompt.enhanced,
        subcategory=subcategory_str,
        techniques=list(attack.techniques),
        error_type=err["error_type"],
        error_message=err["error_message"],
        error_timestamp=err["error_timestamp"],
    )

    entity.evaluations = [
        evaluation_to_entity(name, evaluation)
        for name, evaluation in attack.llm_responses.items()
    ]

    # Collect chatbot_response entities keyed by chatbot name for prompt-hardening linkage
    resp_entities_by_chatbot: dict[str, ChatbotResponseEntity] = {}
    for eval_entity in entity.evaluations:
        if eval_entity.chatbot_response is not None:
            resp_entities_by_chatbot[eval_entity.chatbot_name] = eval_entity.chatbot_response

    entity.detection_results = [
        detection_result_to_entities(
            guardrail_name,
            chatbot_name,
            dr,
            chatbot_response_entity=resp_entities_by_chatbot.get(chatbot_name.value),
        )
        for guardrail_name, per_chatbot in attack.protection.items()
        for chatbot_name, dr in per_chatbot.items()
    ]
    return entity


def case_result_to_entity(tc: TestCaseResult, run_id: str) -> TestCaseEntity:
    gen_err = _error_columns(tc.generation_error)
    enh_err = _error_columns(tc.enhancement_error)
    subcategory_strs = [
        (s.value if hasattr(s, "value") else str(s)) for s in tc.subcategories
    ] if tc.subcategories else []

    entity = TestCaseEntity(
        run_id=run_id,
        category=tc.category.value,
        model_attack_generation=tc.model.attack_and_vulnerability_generation
        if tc.model
        else None,
        subcategories=subcategory_strs,
        generation_error_type=gen_err["error_type"],
        generation_error_message=gen_err["error_message"],
        generation_error_timestamp=gen_err["error_timestamp"],
        enhancement_error_type=enh_err["error_type"],
        enhancement_error_message=enh_err["error_message"],
        enhancement_error_timestamp=enh_err["error_timestamp"],
    )
    entity.attacks = [
        attack_to_entity(k, v) for k, v in tc.attacks.items()
    ]
    return entity


def run_result_to_entity(tr: TestRunResult) -> TestRunEntity:
    entity = TestRunEntity(
        run_id=tr.run_id,
        start_ts=tr.timestamp.start,
        end_ts=tr.timestamp.end,
    )
    entity.test_cases = [case_result_to_entity(tc, tr.run_id) for tc in tr.attack_categories]
    return entity


# ---------------------------------------------------------------------------
# Entity → DTO
# ---------------------------------------------------------------------------


def _entity_to_error(
    error_type: str | None,
    error_message: str | None,
    error_timestamp: datetime | None,
) -> TestErrorInfo | None:
    if error_type is None:
        return None
    return TestErrorInfo(
        error_type=LLMErrorType(error_type),
        message=error_message or "",
        timestamp=error_timestamp or datetime.now(timezone.utc),
    )


def scanner_detail_from_entity(entity: ScannerDetailEntity) -> ScannerDetail:
    return ScannerDetail(
        name=entity.name,
        score=entity.score,
        reason=entity.reason,
        is_valid=entity.is_valid,
        sanitized_input=entity.sanitized_input,
    )


def detection_element_from_entity(
    entity: DetectionElementEntity,
    chatbot_response: ChatbotResponse | None = None,
) -> DetectionElement:
    error = _entity_to_error(entity.error_type, entity.error_message, entity.error_timestamp)
    detected_type: Category | str | None = None
    if entity.detected_type is not None:
        try:
            detected_type = Category(entity.detected_type)
        except ValueError:
            detected_type = entity.detected_type

    if chatbot_response is not None:
        return PromptHardeningDetectionElement(
            success=entity.success,
            detected_type=detected_type,
            score=entity.score,
            judge_raw_response=entity.judge_raw_response,
            latency=entity.latency,
            scanner_details=[scanner_detail_from_entity(s) for s in entity.scanner_details],
            error=error,
            chatbot_response=chatbot_response,
        )

    return DetectionElement(
        success=entity.success,
        detected_type=detected_type,
        score=entity.score,
        judge_raw_response=entity.judge_raw_response,
        latency=entity.latency,
        scanner_details=[scanner_detail_from_entity(s) for s in entity.scanner_details],
        error=error,
    )


def chatbot_response_from_entity(entity: ChatbotResponseEntity) -> ChatbotResponse:
    error = _entity_to_error(entity.error_type, entity.error_message, entity.error_timestamp)
    tool_args = entity.tool_args
    rag_context: RagContext | None = None
    if entity.rag_nodes is not None or entity.rag_embedding_model is not None:
        rag_context = RagContext(
            embedding_model=entity.rag_embedding_model,
            nodes=entity.rag_nodes or [],
        )
    doc_context: DocumentContext | None = None
    if entity.document_content is not None:
        doc_context = DocumentContext(document=entity.document_content)

    return ChatbotResponse(
        prompt=entity.prompt,
        raw_prompt=entity.raw_prompt,
        response=entity.response,
        system_prompt=entity.system_prompt,
        tool=ToolInfo(
            tool_called=entity.tool_called,
            tool_name=entity.tool_name,
            tool_args=tool_args,
        ),
        prompt_tokens=entity.prompt_tokens,
        response_tokens=entity.response_tokens,
        rag_context=rag_context,
        document_content=doc_context,
        file_path=entity.file_path,
        error=error,
    )


def evaluation_from_entity(entity: ChatbotResponseEvaluationEntity) -> ChatbotResponseEvaluation:
    error = _entity_to_error(entity.error_type, entity.error_message, entity.error_timestamp)
    resp = (
        chatbot_response_from_entity(entity.chatbot_response)
        if entity.chatbot_response is not None
        else ChatbotResponse.from_error(TestErrorInfo(error_type=LLMErrorType.UNKNOWN, message="missing"))
    )
    return ChatbotResponseEvaluation(
        chatbot_response=resp,
        score=entity.score,
        reason=entity.reason,
        success=entity.success,
        metric=entity.metric,
        error=error,
    )


def detection_result_from_entity(
    entity: DetectionResultEntity,
    resp_by_chatbot_resp_id: dict[int, ChatbotResponse],
) -> tuple[str, ChatbotName, DetectionResult]:
    input_el: DetectionElementEntity | None = None
    output_el: DetectionElementEntity | None = None
    for de in entity.detection_elements:
        if de.stage == "input":
            input_el = de
        else:
            output_el = de

    assert input_el is not None and output_el is not None, (
        f"DetectionResultEntity {entity.id} is missing input or output element"
    )

    phc: ChatbotResponse | None = None
    if entity.guardrail_name == _PROMPT_HARDENING:
        # Prefer the in-memory relationship object; fall back to ID lookup
        if output_el.prompt_hardening_chatbot_response is not None:
            phc = chatbot_response_from_entity(output_el.prompt_hardening_chatbot_response)
        elif output_el.chatbot_response_id is not None:
            phc = resp_by_chatbot_resp_id.get(output_el.chatbot_response_id)

    input_dto = detection_element_from_entity(input_el)
    output_dto = detection_element_from_entity(output_el, phc if entity.guardrail_name == _PROMPT_HARDENING else None)

    try:
        chatbot = ChatbotName(entity.chatbot_name)
    except ValueError:
        chatbot = entity.chatbot_name  # type: ignore[assignment]

    return entity.guardrail_name, chatbot, DetectionResult(
        input_detection=input_dto,
        output_detection=output_dto,
    )


def attack_from_entity(entity: AttackEntity) -> tuple[str, Attack]:
    """Return (uuid_key, Attack DTO). Key is a placeholder since the original UUID is not stored."""
    import uuid as _uuid
    key = str(_uuid.uuid4())

    err = _entity_to_error(entity.error_type, entity.error_message, entity.error_timestamp)

    llm_responses: dict[ChatbotName, ChatbotResponseEvaluation] = {}
    resp_by_chatbot_resp_id: dict[int, ChatbotResponse] = {}
    for eval_entity in entity.evaluations:
        try:
            cname = ChatbotName(eval_entity.chatbot_name)
        except ValueError:
            cname = eval_entity.chatbot_name  # type: ignore[assignment]
        dto = evaluation_from_entity(eval_entity)
        llm_responses[cname] = dto
        if eval_entity.chatbot_response is not None:
            resp_by_chatbot_resp_id[eval_entity.chatbot_response.id] = dto.chatbot_response

    protection: dict[str, dict[ChatbotName, DetectionResult]] = {}
    for dr_entity in entity.detection_results:
        g_name, c_name, dr = detection_result_from_entity(dr_entity, resp_by_chatbot_resp_id)
        protection.setdefault(g_name, {})[c_name] = dr

    try:
        severity = Severity(entity.severity)
    except ValueError:
        severity = Severity.UNSAFE

    subcategory = None
    if entity.subcategory is not None:
        subcategory = entity.subcategory

    attack = Attack(
        category=entity.category,
        subcategory=subcategory,
        techniques=list(entity.techniques or []),
        severity=severity,
        prompt=PromptVariants(baseline=entity.prompt_baseline, enhanced=entity.prompt_enhanced),
        llm_responses=llm_responses,
        protection=protection,
        error=err,
    )
    return key, attack


def case_result_from_entity(entity: TestCaseEntity) -> TestCaseResult:
    try:
        category = Category(entity.category)
    except ValueError:
        category = entity.category  # type: ignore[assignment]

    gen_err = _entity_to_error(
        entity.generation_error_type,
        entity.generation_error_message,
        entity.generation_error_timestamp,
    )
    enh_err = _entity_to_error(
        entity.enhancement_error_type,
        entity.enhancement_error_message,
        entity.enhancement_error_timestamp,
    )

    attacks: dict[str, Attack] = {}
    for att_entity in entity.attacks:
        key, att_dto = attack_from_entity(att_entity)
        attacks[key] = att_dto

    return TestCaseResult(
        category=category,
        subcategories=list(entity.subcategories or []),
        model=TestCaseResult.ModelInfo(
            attack_and_vulnerability_generation=entity.model_attack_generation
        ),
        attacks=attacks,
        generation_error=gen_err,
        enhancement_error=enh_err,
    )


def run_result_from_entity(entity: TestRunEntity) -> TestRunResult:
    return TestRunResult(
        run_id=entity.run_id,
        timestamp=TestRunTimestamp(start=entity.start_ts, end=entity.end_ts or entity.start_ts),
        attack_categories=[case_result_from_entity(tc) for tc in entity.test_cases],
    )
