#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

import csv
import json

from testframework.custom_attack_techniques.techniques import TECHNIQUE_BASELINE
from testframework.reporting.run_summary import RunSummary


def _detection(*, success, scanner_details=None, error=None):
    return {
        "success": success,
        "scanner_details": scanner_details or [],
        "error": error,
    }


def _attack(*, severity: str, chatbot_success: bool, input_success: bool, output_success: bool):
    return {
        "category": "privacy",
        "techniques": ["Technique A"],
        "severity": severity,
        "llm_responses": {
            "MODEL_A": {
                "success": chatbot_success,
                "error": None,
                "chatbot_response": {
                    "error": None,
                },
            }
        },
        "protection": {
            "prompt_hardening": {
                "MODEL_A": {
                    "input_detection": _detection(success=False),
                    "output_detection": _detection(success=output_success),
                }
            },
            "llm_guard": {
                "MODEL_A": {
                    "input_detection": _detection(success=input_success),
                    "output_detection": _detection(success=output_success),
                }
            },
        },
    }


def _write_summary_run(tmp_path, *, consider_chatbot_success: bool) -> tuple[dict, object]:
    run_dir = tmp_path / "run"
    testcase_dir = run_dir / "testcase"
    testcase_dir.mkdir(parents=True)

    testcase = {
        "category": "privacy",
        "attacks": {
            "unsafe-chatbot-blocks": _attack(
                severity="unsafe",
                chatbot_success=True,
                input_success=True,
                output_success=True,
            ),
            "safe-chatbot-overblocks": _attack(
                severity="safe",
                chatbot_success=False,
                input_success=True,
                output_success=True,
            ),
        },
    }
    (testcase_dir / "privacy.json").write_text(
        json.dumps(testcase),
        encoding="utf-8",
    )

    summary = RunSummary(
        run_dir,
        consider_chatbot_success=consider_chatbot_success,
    ).build()
    return summary, run_dir


def test_run_summary_keeps_legacy_guardrail_overall_semantics_by_default(tmp_path):
    summary, _ = _write_summary_run(
        tmp_path,
        consider_chatbot_success=False,
    )

    model_summary = summary["MODEL_A"]

    baseline_node = model_summary["baseline"]
    assert baseline_node["TP"] == 1
    assert baseline_node["FP"] == 1

    prompt_hardening_node = model_summary["prompt_hardening"]
    assert prompt_hardening_node["TP"] == 1
    assert prompt_hardening_node["TN"] == 1

    llm_guard_node = model_summary["llm_guard_overall"]
    assert llm_guard_node["FN"] == 1
    assert llm_guard_node["TN"] == 1


def test_run_summary_can_consider_chatbot_success_for_guardrail_overall(tmp_path):
    summary, _ = _write_summary_run(
        tmp_path,
        consider_chatbot_success=True,
    )

    model_summary = summary["MODEL_A"]

    baseline_node = model_summary["baseline"]
    assert baseline_node["TP"] == 1
    assert baseline_node["FP"] == 1

    prompt_hardening_node = model_summary["prompt_hardening"]
    assert prompt_hardening_node["TP"] == 1
    assert prompt_hardening_node["TN"] == 1

    llm_guard_node = model_summary["llm_guard_overall"]
    assert llm_guard_node["TP"] == 1
    assert llm_guard_node["FP"] == 1


def test_run_summary_csv_exports_reflect_chatbot_success_mode(tmp_path):
    _, run_dir = _write_summary_run(
        tmp_path,
        consider_chatbot_success=True,
    )

    output_path = tmp_path / "summary.json"
    RunSummary(
        run_dir,
        consider_chatbot_success=True,
    ).write(output_path)

    csv_path = tmp_path / "summary" / "MODEL_A" / "summary.csv"
    with csv_path.open("r", encoding="utf-8", newline="") as file_handle:
        rows = list(csv.DictReader(file_handle))

    rows_by_node = {
        row["node"]: row
        for row in rows
        if row["scope"] == "overall"
    }

    assert rows_by_node["baseline"]["tp"] == "1"
    assert rows_by_node["baseline"]["fp"] == "1"
    assert rows_by_node["prompt_hardening"]["tp"] == "1"
    assert rows_by_node["prompt_hardening"]["tn"] == "1"
    assert rows_by_node["llm_guard_overall"]["tp"] == "1"
    assert rows_by_node["llm_guard_overall"]["fp"] == "1"


# ---------------------------------------------------------------------------
# _get_confusion_matrix_label
# ---------------------------------------------------------------------------

def test_get_confusion_matrix_label_unsafe_correct_is_tp():
    assert RunSummary._get_confusion_matrix_label(True, True) == "TP"


def test_get_confusion_matrix_label_unsafe_incorrect_is_fn():
    assert RunSummary._get_confusion_matrix_label(True, False) == "FN"


def test_get_confusion_matrix_label_safe_correct_is_tn():
    assert RunSummary._get_confusion_matrix_label(False, True) == "TN"


def test_get_confusion_matrix_label_safe_incorrect_is_fp():
    assert RunSummary._get_confusion_matrix_label(False, False) == "FP"


# ---------------------------------------------------------------------------
# _is_total_guardrail_correct
# ---------------------------------------------------------------------------

def test_is_total_guardrail_correct_unsafe_flagged():
    assert RunSummary._is_total_guardrail_correct(True, False) is True


def test_is_total_guardrail_correct_unsafe_not_flagged():
    assert RunSummary._is_total_guardrail_correct(True, True) is False


def test_is_total_guardrail_correct_safe_not_flagged():
    assert RunSummary._is_total_guardrail_correct(False, True) is True


def test_is_total_guardrail_correct_safe_flagged():
    assert RunSummary._is_total_guardrail_correct(False, False) is False


def test_is_total_guardrail_correct_unsafe_flagged_chatbot_safe():
    assert RunSummary._is_total_guardrail_correct(True, False, chatbot_safe_response=True) is True


def test_is_total_guardrail_correct_unsafe_not_flagged_chatbot_safe():
    # Chatbot safe response compensates for the scanner not flagging
    assert RunSummary._is_total_guardrail_correct(True, True, chatbot_safe_response=True) is True


def test_is_total_guardrail_correct_safe_not_flagged_chatbot_safe():
    assert RunSummary._is_total_guardrail_correct(False, True, chatbot_safe_response=True) is True


def test_is_total_guardrail_correct_safe_flagged_chatbot_unsafe():
    assert RunSummary._is_total_guardrail_correct(False, False, chatbot_safe_response=False) is False


# ---------------------------------------------------------------------------
# Helpers shared by the build() tests below
# ---------------------------------------------------------------------------

def _build_testcase_file(tmp_path, testcase_data):
    run_dir = tmp_path / "run"
    testcase_dir = run_dir / "testcase"
    testcase_dir.mkdir(parents=True)
    (testcase_dir / "result.json").write_text(json.dumps(testcase_data), encoding="utf-8")
    return run_dir


def _simple_attack(severity="unsafe", techniques=None, category="privacy"):
    return {
        "category": category,
        "techniques": techniques or ["Technique A"],
        "severity": severity,
        "llm_responses": {
            "MODEL_A": {
                "success": False,
                "error": None,
                "chatbot_response": {"error": None},
            }
        },
        "protection": {},
    }


# ---------------------------------------------------------------------------
# build() – benign prompt handling
# ---------------------------------------------------------------------------

def test_build_skips_benign_attack_with_non_baseline_technique(tmp_path):
    attack = _simple_attack(severity="safe", techniques=["Roleplay"], category="benign")
    run_dir = _build_testcase_file(tmp_path, {"category": "benign", "attacks": {"a": attack}})
    summary = RunSummary(run_dir).build()
    assert summary == {}


def test_build_includes_benign_attack_with_baseline_technique(tmp_path):
    attack = _simple_attack(
        severity="safe",
        techniques=[TECHNIQUE_BASELINE],
        category="benign",
    )
    run_dir = _build_testcase_file(tmp_path, {"category": "benign", "attacks": {"a": attack}})
    summary = RunSummary(run_dir).build()
    assert "MODEL_A" in summary
    assert summary["MODEL_A"]["baseline"]["count"] == 1


def test_build_includes_benign_attack_when_legacy_no_technique_label_is_used(tmp_path):
    attack = _simple_attack(
        severity="safe",
        techniques=["N/A"],
        category="benign",
    )
    run_dir = _build_testcase_file(tmp_path, {"category": "benign", "attacks": {"a": attack}})
    summary = RunSummary(run_dir).build()
    assert "MODEL_A" in summary
    assert summary["MODEL_A"]["baseline"]["count"] == 1


def test_build_includes_benign_attack_when_techniques_key_is_missing(tmp_path):
    attack = _simple_attack(
        severity="safe",
        techniques=[TECHNIQUE_BASELINE],
        category="benign",
    )
    attack.pop("techniques")
    run_dir = _build_testcase_file(tmp_path, {"category": "benign", "attacks": {"a": attack}})
    summary = RunSummary(run_dir).build()
    assert "MODEL_A" in summary
    assert summary["MODEL_A"]["baseline"]["count"] == 1


# ---------------------------------------------------------------------------
# build() – Lakera scanner name collapsing
# ---------------------------------------------------------------------------

def test_build_collapses_lakera_sub_scanner_names(tmp_path):
    # Both sub-scanner names collapse to "prompt_injection" via the '/' split.
    # The attack must be counted exactly once in lakera_guard_overall.
    attack = {
        "category": "privacy",
        "techniques": ["Technique A"],
        "severity": "unsafe",
        "llm_responses": {
            "MODEL_A": {
                "success": False,
                "error": None,
                "chatbot_response": {"error": None},
            }
        },
        "protection": {
            "lakera_guard": {
                "MODEL_A": {
                    "input_detection": _detection(
                        success=False,
                        scanner_details=[
                            {"name": "prompt_injection/direct", "is_valid": False},
                            {"name": "prompt_injection/indirect", "is_valid": False},
                        ],
                    ),
                    "output_detection": _detection(success=True),
                }
            }
        },
    }
    run_dir = _build_testcase_file(tmp_path, {"category": "privacy", "attacks": {"a": attack}})
    summary = RunSummary(run_dir, exclude_scanners=True).build()

    lakera_node = summary["MODEL_A"]["lakera_guard_overall"]
    assert lakera_node["count"] == 1


# ---------------------------------------------------------------------------
# build() – error handling
# ---------------------------------------------------------------------------

def test_build_adds_error_when_baseline_response_has_error(tmp_path):
    attack = {
        "category": "privacy",
        "techniques": ["Technique A"],
        "severity": "unsafe",
        "llm_responses": {
            "MODEL_A": {
                "success": False,
                "error": "Connection failed",
                "chatbot_response": {"error": None},
            }
        },
        "protection": {},
    }
    run_dir = _build_testcase_file(tmp_path, {"category": "privacy", "attacks": {"a": attack}})
    summary = RunSummary(run_dir).build()
    assert "MODEL_A" in summary
    assert "privacy" in summary["MODEL_A"]["_errors"]


def test_build_adds_error_when_detection_has_error(tmp_path):
    attack = {
        "category": "privacy",
        "techniques": ["Technique A"],
        "severity": "unsafe",
        "llm_responses": {
            "MODEL_A": {
                "success": False,
                "error": None,
                "chatbot_response": {"error": None},
            }
        },
        "protection": {
            "llm_guard": {
                "MODEL_A": {
                    "input_detection": _detection(success=False, error="Scanner error"),
                    "output_detection": _detection(success=True),
                }
            }
        },
    }
    run_dir = _build_testcase_file(tmp_path, {"category": "privacy", "attacks": {"a": attack}})
    summary = RunSummary(run_dir).build()
    assert "privacy" in summary["MODEL_A"]["_errors"]


# ---------------------------------------------------------------------------
# _write_model_csv_exports / _build_summary_csv_rows
# ---------------------------------------------------------------------------

def _build_single_attack_run(tmp_path):
    run_dir = tmp_path / "run"
    testcase_dir = run_dir / "testcase"
    testcase_dir.mkdir(parents=True)
    testcase = {
        "category": "privacy",
        "attacks": {
            "attack_1": _simple_attack(severity="unsafe", techniques=["Technique A"]),
        },
    }
    (testcase_dir / "privacy.json").write_text(json.dumps(testcase), encoding="utf-8")
    return run_dir


def test_write_produces_csv_with_attack_category_rows(tmp_path):
    run_dir = _build_single_attack_run(tmp_path)
    output_path = tmp_path / "summary.json"
    RunSummary(run_dir).write(output_path)

    csv_path = tmp_path / "summary" / "MODEL_A" / "summary.csv"
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    assert "attack_category" in [row["scope"] for row in rows]


def test_write_produces_csv_with_technique_rows(tmp_path):
    run_dir = _build_single_attack_run(tmp_path)
    output_path = tmp_path / "summary.json"
    RunSummary(run_dir).write(output_path)

    csv_path = tmp_path / "summary" / "MODEL_A" / "summary.csv"
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    assert "technique" in [row["scope"] for row in rows]
