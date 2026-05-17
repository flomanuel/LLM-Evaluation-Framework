import json

from testframework.reporting.scanner_summary import ScannerSummary


def _detection(*, scanner_details=None, error=None):
    return {
        "success": True,
        "scanner_details": scanner_details or [],
        "error": error,
    }


def _attack(*, severity: str, input_scanners: list[dict], output_scanners: list[dict], error: str | None = None):
    return {
        "severity": severity,
        "protection": {
            "prompt_hardening": {
                "MODEL_A": {
                    "input_detection": _detection(),
                    "output_detection": _detection(),
                }
            },
            "lakera_guard": {
                "MODEL_A": {
                    "input_detection": _detection(scanner_details=input_scanners, error=error),
                    "output_detection": _detection(scanner_details=output_scanners, error=error),
                }
            },
        },
    }


def test_scanner_summary_outputs_per_scanner_counts(tmp_path, capsys):
    # build_rows() prints CSV-formatted results to stdout.
    run_dir = tmp_path / "run"
    testcase_dir = run_dir / "testcase"
    testcase_dir.mkdir(parents=True)

    testcase = {
        "attacks": {
            "unsafe-detected-on-input": _attack(
                severity="unsafe",
                input_scanners=[{"name": "prompt_injection", "is_valid": False}],
                output_scanners=[{"name": "toxicity", "is_valid": True}],
            ),
            "unsafe-missed": _attack(
                severity="unsafe",
                input_scanners=[{"name": "prompt_injection", "is_valid": True}],
                output_scanners=[{"name": "toxicity", "is_valid": True}],
            ),
            "safe-overblocked-on-output": _attack(
                severity="safe",
                input_scanners=[{"name": "prompt_injection", "is_valid": True}],
                output_scanners=[{"name": "toxicity", "is_valid": False}],
            ),
            "safe-clean": _attack(
                severity="safe",
                input_scanners=[{"name": "prompt_injection", "is_valid": True}],
                output_scanners=[{"name": "toxicity", "is_valid": True}],
            ),
            "stage-error": _attack(
                severity="unsafe",
                input_scanners=[{"name": "prompt_injection", "is_valid": False}],
                output_scanners=[{"name": "toxicity", "is_valid": False}],
                error="boom",
            ),
        },
    }
    (testcase_dir / "privacy.json").write_text(json.dumps(testcase), encoding="utf-8")

    ScannerSummary(run_dir).build_rows()

    captured = capsys.readouterr()
    lines = [l for l in captured.out.strip().split("\n") if l]
    # header + 2 scanner rows
    assert len(lines) == 3
    assert lines[0] == "chatbot,guardrail,stage,scanner_detail,count,TP,FP,TN,FN,errors"

    rows_by_key = {}
    for line in lines[1:]:
        parts = line.split(",")
        rows_by_key[(parts[2], parts[3])] = parts  # keyed by (stage, scanner_name)

    # prompt_injection input: count=4, TP=1, FP=0, TN=2, FN=1
    pi = rows_by_key[("input", "prompt_injection")]
    assert pi[0] == "MODEL_A"
    assert pi[1] == "lakera_guard"
    assert pi[4] == "4"  # count
    assert pi[5] == "1"  # TP
    assert pi[6] == "0"  # FP
    assert pi[7] == "2"  # TN
    assert pi[8] == "1"  # FN

    # toxicity output: count=4, TP=0, FP=1, TN=1, FN=2
    tox = rows_by_key[("output", "toxicity")]
    assert tox[1] == "lakera_guard"
    assert tox[4] == "4"  # count
    assert tox[5] == "0"  # TP
    assert tox[6] == "1"  # FP
    assert tox[7] == "1"  # TN
    assert tox[8] == "2"  # FN


# ---------------------------------------------------------------------------
# _get_confusion_matrix_label
# ---------------------------------------------------------------------------

def test_scanner_summary_confusion_matrix_unsafe_detected_is_tp():
    assert ScannerSummary._get_confusion_matrix_label(is_unsafe=True, was_detected=True) == "TP"


def test_scanner_summary_confusion_matrix_unsafe_not_detected_is_fn():
    assert ScannerSummary._get_confusion_matrix_label(is_unsafe=True, was_detected=False) == "FN"


def test_scanner_summary_confusion_matrix_safe_detected_is_fp():
    assert ScannerSummary._get_confusion_matrix_label(is_unsafe=False, was_detected=True) == "FP"


def test_scanner_summary_confusion_matrix_safe_not_detected_is_tn():
    assert ScannerSummary._get_confusion_matrix_label(is_unsafe=False, was_detected=False) == "TN"


# ---------------------------------------------------------------------------
# _ensure_counts
# ---------------------------------------------------------------------------

def test_ensure_counts_creates_zeroed_entry_for_new_key():
    summary = {}
    counts = ScannerSummary._ensure_counts(
        summary,
        model_name="MODEL_A",
        guardrail_name="llm_guard",
        stage="input",
        scanner_name="prompt_injection",
    )
    assert counts["count"] == 0
    assert counts["TP"] == 0
    assert counts["FP"] == 0
    assert counts["TN"] == 0
    assert counts["FN"] == 0
    assert counts["errors"] == 0


def test_ensure_counts_returns_existing_entry():
    summary = {}
    counts1 = ScannerSummary._ensure_counts(summary, "A", "g", "input", "scanner")
    counts1["count"] = 5
    counts2 = ScannerSummary._ensure_counts(summary, "A", "g", "input", "scanner")
    assert counts2["count"] == 5
    assert counts1 is counts2


# ---------------------------------------------------------------------------
# build_rows() – extended cases (verified via stdout)
# ---------------------------------------------------------------------------

def test_build_rows_skips_prompt_hardening_guardrail(tmp_path, capsys):
    run_dir = tmp_path / "run"
    testcase_dir = run_dir / "testcase"
    testcase_dir.mkdir(parents=True)
    testcase = {
        "attacks": {
            "a": {
                "severity": "unsafe",
                "protection": {
                    "prompt_hardening": {
                        "MODEL_A": {
                            "input_detection": _detection(),
                            "output_detection": _detection(),
                        }
                    }
                },
            }
        }
    }
    (testcase_dir / "result.json").write_text(json.dumps(testcase), encoding="utf-8")
    ScannerSummary(run_dir).build_rows()
    lines = [l for l in capsys.readouterr().out.strip().split("\n") if l]
    # Only header — prompt_hardening is skipped entirely
    assert len(lines) == 1


def test_build_rows_skips_detections_with_errors(tmp_path, capsys):
    run_dir = tmp_path / "run"
    testcase_dir = run_dir / "testcase"
    testcase_dir.mkdir(parents=True)
    testcase = {
        "attacks": {
            "a": {
                "severity": "unsafe",
                "protection": {
                    "lakera_guard": {
                        "MODEL_A": {
                            "input_detection": _detection(
                                scanner_details=[{"name": "pi", "is_valid": False}],
                                error="boom",
                            ),
                            "output_detection": _detection(),
                        }
                    }
                },
            }
        }
    }
    (testcase_dir / "result.json").write_text(json.dumps(testcase), encoding="utf-8")
    ScannerSummary(run_dir).build_rows()
    lines = [l for l in capsys.readouterr().out.strip().split("\n") if l]
    # Only header — errored detection is skipped
    assert len(lines) == 1


def test_build_rows_multiple_models_produce_separate_rows(tmp_path, capsys):
    run_dir = tmp_path / "run"
    testcase_dir = run_dir / "testcase"
    testcase_dir.mkdir(parents=True)
    scanner_detail = [{"name": "prompt_injection", "is_valid": True}]
    testcase = {
        "attacks": {
            "a": {
                "severity": "safe",
                "protection": {
                    "lakera_guard": {
                        "MODEL_A": {
                            "input_detection": _detection(scanner_details=scanner_detail),
                            "output_detection": _detection(),
                        },
                        "MODEL_B": {
                            "input_detection": _detection(scanner_details=scanner_detail),
                            "output_detection": _detection(),
                        },
                    }
                },
            }
        }
    }
    (testcase_dir / "result.json").write_text(json.dumps(testcase), encoding="utf-8")
    ScannerSummary(run_dir).build_rows()
    lines = [l for l in capsys.readouterr().out.strip().split("\n") if l]
    # header + MODEL_A row + MODEL_B row
    assert len(lines) == 3
    models = {l.split(",")[0] for l in lines[1:]}
    assert "MODEL_A" in models
    assert "MODEL_B" in models
