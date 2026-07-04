#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

"""
Integration tests for the historical JSON importer.

Tests cover: happy-path import, idempotency, --force re-import, analysis
creation, and tolerant deserialization of legacy JSON shapes.
"""

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy.orm import sessionmaker

import testframework.persistence.session as _session_module
from testframework.enums import Category, ChatbotName, Severity
from testframework.models import (
    Attack,
    ChatbotResponse,
    ChatbotResponseEvaluation,
    DetectionElement,
    DetectionResult,
    PromptHardeningDetectionElement,
    PromptVariants,
    RagContext,
    ScannerDetail,
    TestCaseResult,
    TestRunResult,
    TestRunTimestamp,
    ToolInfo,
)
from testframework.persistence.importer import ImportStats, deserialize_run, import_runs
from testframework.persistence.service.test_run_service import TestRunService

_NOW = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def wire_session(db_engine):
    _session_module.engine = db_engine
    _session_module.Session = sessionmaker(db_engine, autoflush=False)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _minimal_run() -> TestRunResult:
    """Build a minimal TestRunResult with one test case and one attack."""
    return TestRunResult(
        run_id=str(uuid4()),
        timestamp=TestRunTimestamp(start=_NOW, end=_NOW),
        attack_categories=[
            TestCaseResult(
                category=Category.ILLEGAL_ACTIVITY,
                subcategories=[],
                model=TestCaseResult.ModelInfo(attack_and_vulnerability_generation="gpt-4"),
                attacks={
                    str(uuid4()): Attack(
                        category=Category.ILLEGAL_ACTIVITY.value,
                        subcategory=None,
                        techniques=["TechA"],
                        severity=Severity.UNSAFE,
                        prompt=PromptVariants(baseline="base", enhanced="enhanced"),
                        llm_responses={
                            ChatbotName.DUMMY: ChatbotResponseEvaluation(
                                chatbot_response=ChatbotResponse(
                                    prompt="p",
                                    raw_prompt="rp",
                                    response="r",
                                    system_prompt="sys",
                                    tool=ToolInfo(tool_called=False),
                                    prompt_tokens=1,
                                    response_tokens=1,
                                    rag_context=None,
                                    document_content=None,
                                ),
                                score=0.5,
                                reason="ok",
                                success=True,
                                metric="M",
                            )
                        },
                        protection={
                            "llm_guard": {
                                ChatbotName.DUMMY: DetectionResult(
                                    input_detection=DetectionElement(
                                        success=True,
                                        detected_type=None,
                                        score=0.9,
                                        judge_raw_response="raw",
                                        latency=0.1,
                                        scanner_details=[
                                            ScannerDetail(
                                                name="s",
                                                score=0.5,
                                                reason="r",
                                                is_valid=True,
                                                sanitized_input="",
                                            )
                                        ],
                                    ),
                                    output_detection=DetectionElement(
                                        success=True,
                                        detected_type=None,
                                        score=0.9,
                                        judge_raw_response="raw",
                                        latency=0.1,
                                        scanner_details=[],
                                    ),
                                )
                            }
                        },
                    )
                },
            )
        ],
    )


def _write_result_json(run: TestRunResult, tmp_path: Path) -> Path:
    """Write result.json in the same format as storage.save_test_run."""
    run_dir = tmp_path / run.run_id
    run_dir.mkdir(parents=True)
    path = run_dir / "result.json"
    path.write_text(json.dumps(asdict(run), default=str, indent=2), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Deserialization (pure unit tests — no DB)
# ---------------------------------------------------------------------------

class TestDeserializeRun:
    def test_round_trip(self):
        """Deserializing a fresh asdict() produces matching metadata."""
        run = _minimal_run()
        data = json.loads(json.dumps(asdict(run), default=str))
        restored = deserialize_run(data)
        assert restored.run_id == run.run_id
        assert len(restored.attack_categories) == 1
        tc = restored.attack_categories[0]
        assert tc.category == Category.ILLEGAL_ACTIVITY
        assert len(tc.attacks) == 1

    def test_attack_fields_preserved(self):
        run = _minimal_run()
        data = json.loads(json.dumps(asdict(run), default=str))
        restored = deserialize_run(data)
        attack = next(iter(restored.attack_categories[0].attacks.values()))
        assert attack.severity == Severity.UNSAFE
        assert attack.techniques == ["TechA"]
        assert attack.prompt.baseline == "base"

    def test_scanner_details_preserved(self):
        run = _minimal_run()
        data = json.loads(json.dumps(asdict(run), default=str))
        restored = deserialize_run(data)
        attack = next(iter(restored.attack_categories[0].attacks.values()))
        det = attack.protection["llm_guard"][ChatbotName.DUMMY]
        assert len(det.input_detection.scanner_details) == 1
        assert det.input_detection.scanner_details[0].name == "s"

    def test_legacy_category_dot_format(self):
        """Category stored as 'Category.ILLEGAL_ACTIVITY' (old Python str(enum))."""
        run = _minimal_run()
        data = json.loads(json.dumps(asdict(run), default=str))
        data["attack_categories"][0]["category"] = "Category.ILLEGAL_ACTIVITY"
        restored = deserialize_run(data)
        assert restored.attack_categories[0].category == Category.ILLEGAL_ACTIVITY

    def test_legacy_severity_dot_format(self):
        """Severity stored as 'Severity.UNSAFE' (old Python str(enum))."""
        run = _minimal_run()
        data = json.loads(json.dumps(asdict(run), default=str))
        attack_key = next(iter(data["attack_categories"][0]["attacks"]))
        data["attack_categories"][0]["attacks"][attack_key]["severity"] = "Severity.UNSAFE"
        restored = deserialize_run(data)
        attack = next(iter(restored.attack_categories[0].attacks.values()))
        assert attack.severity == Severity.UNSAFE

    def test_missing_optional_fields_use_defaults(self):
        """Fields like file_path, rag_context, latency may be absent."""
        run = _minimal_run()
        data = json.loads(json.dumps(asdict(run), default=str))
        attack_key = next(iter(data["attack_categories"][0]["attacks"]))
        attack_data = data["attack_categories"][0]["attacks"][attack_key]
        cr = attack_data["llm_responses"]["DUMMY"]["chatbot_response"]
        cr.pop("file_path", None)
        cr.pop("rag_context", None)
        det = attack_data["protection"]["llm_guard"]["DUMMY"]["input_detection"]
        det.pop("latency", None)
        restored = deserialize_run(data)
        attack = next(iter(restored.attack_categories[0].attacks.values()))
        assert attack.llm_responses[ChatbotName.DUMMY].chatbot_response.file_path is None
        assert attack.protection["llm_guard"][ChatbotName.DUMMY].input_detection.latency is None

    def test_prompt_hardening_output_with_chatbot_response(self):
        """PromptHardeningDetectionElement with chatbot_response field is deserialized correctly."""
        run = _minimal_run()
        data = json.loads(json.dumps(asdict(run), default=str))
        tc = data["attack_categories"][0]
        attack_key = next(iter(tc["attacks"]))
        # Inject a prompt_hardening guardrail with chatbot_response in output detection
        tc["attacks"][attack_key]["protection"]["prompt_hardening"] = {
            "DUMMY": {
                "input_detection": {
                    "success": False,
                    "detected_type": None,
                    "score": 0.0,
                    "judge_raw_response": "",
                    "latency": None,
                    "scanner_details": [],
                    "error": None,
                },
                "output_detection": {
                    "success": True,
                    "detected_type": None,
                    "score": 0.0,
                    "judge_raw_response": "",
                    "latency": None,
                    "scanner_details": [],
                    "error": None,
                    "chatbot_response": {
                        "prompt": "ph",
                        "raw_prompt": "rph",
                        "response": "resp",
                        "system_prompt": "sys",
                        "tool": {"tool_called": False, "tool_name": None, "tool_args": None},
                        "prompt_tokens": 1,
                        "response_tokens": 1,
                        "rag_context": None,
                        "document_content": None,
                        "file_path": None,
                        "error": None,
                    },
                },
            }
        }
        restored = deserialize_run(data)
        attack = next(iter(restored.attack_categories[0].attacks.values()))
        ph_det = attack.protection["prompt_hardening"][ChatbotName.DUMMY]
        assert isinstance(ph_det.output_detection, PromptHardeningDetectionElement)
        assert ph_det.output_detection.chatbot_response is not None
        assert ph_det.output_detection.chatbot_response.prompt == "ph"


# ---------------------------------------------------------------------------
# Integration tests (require DB)
# ---------------------------------------------------------------------------

class TestImportRuns:
    def test_import_single_run(self, tmp_path):
        run = _minimal_run()
        _write_result_json(run, tmp_path)

        stats = import_runs(runs_dir=tmp_path)

        assert stats.imported == 1
        assert stats.skipped == 0
        assert stats.failed == 0
        assert TestRunService().exists(run.run_id)

    def test_import_idempotent_skips_existing(self, tmp_path):
        run = _minimal_run()
        _write_result_json(run, tmp_path)

        import_runs(runs_dir=tmp_path)
        stats = import_runs(runs_dir=tmp_path)  # second pass

        assert stats.imported == 0
        assert stats.skipped == 1

    def test_import_force_reimports(self, tmp_path):
        run = _minimal_run()
        _write_result_json(run, tmp_path)

        import_runs(runs_dir=tmp_path)
        stats = import_runs(runs_dir=tmp_path, force=True)

        assert stats.imported == 1
        assert stats.skipped == 0

    def test_import_empty_directory(self, tmp_path):
        stats = import_runs(runs_dir=tmp_path)
        assert stats.imported == 0
        assert stats.failed == 0

    def test_import_multiple_runs(self, tmp_path):
        runs = [_minimal_run() for _ in range(3)]
        for r in runs:
            _write_result_json(r, tmp_path)

        stats = import_runs(runs_dir=tmp_path)

        assert stats.imported == 3
        for r in runs:
            assert TestRunService().exists(r.run_id)

    def test_import_creates_analysis_run(self, tmp_path):
        """import_runs with reanalyze=True (default) creates an analysis_run."""
        from testframework.persistence.repository.analysis_repository import AnalysisRepository
        import testframework.persistence.session as _sm

        run = _minimal_run()
        _write_result_json(run, tmp_path)
        import_runs(runs_dir=tmp_path, reanalyze=True)

        with _sm.Session() as session:
            analyses = AnalysisRepository(session).find_by_run_id(run.run_id)
        assert len(analyses) == 1

    def test_import_no_reanalyze_skips_analysis(self, tmp_path):
        """import_runs with reanalyze=False does not create an analysis_run."""
        from testframework.persistence.repository.analysis_repository import AnalysisRepository
        import testframework.persistence.session as _sm

        run = _minimal_run()
        _write_result_json(run, tmp_path)
        import_runs(runs_dir=tmp_path, reanalyze=False)

        with _sm.Session() as session:
            analyses = AnalysisRepository(session).find_by_run_id(run.run_id)
        assert len(analyses) == 0

    def test_import_preserves_run_id_and_timestamps(self, tmp_path):
        """The original run_id and start/end timestamps survive the JSON round-trip."""
        run = _minimal_run()
        _write_result_json(run, tmp_path)
        import_runs(runs_dir=tmp_path)

        fetched = TestRunService().get_run(run.run_id)
        assert fetched is not None
        assert fetched.run_id == run.run_id
        assert fetched.timestamp.start == run.timestamp.start
