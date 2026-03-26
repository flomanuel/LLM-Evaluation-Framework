#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from testframework.enums import Severity

TESTCASE_DIR = "testcase"
PROMPT_HARDENING = "prompt_hardening"


class ScannerSummary:
    def __init__(self, run_folder: str | Path) -> None:
        self.run_folder = Path(run_folder)
        self.testcase_dir = self.run_folder / TESTCASE_DIR

    def build_rows(self) -> list[dict[str, Any]]:
        summary: dict[tuple[str, str, str, str], dict[str, int]] = {}

        for testcase_path in sorted(self.testcase_dir.glob("*.json")):
            with testcase_path.open("r", encoding="utf-8") as file_handle:
                testcase_data = json.load(file_handle)

            for attack_data in testcase_data["attacks"].values():
                is_unsafe = str(attack_data["severity"]).lower() == Severity.UNSAFE.value

                for guardrail_name, model_results in attack_data.get("protection", {}).items():
                    if guardrail_name == PROMPT_HARDENING:
                        continue

                    for model_name, detection_result in model_results.items():
                        for stage, detection in (
                                ("input", detection_result["input_detection"]),
                                ("output", detection_result["output_detection"]),
                        ):
                            if detection["error"] is not None:
                                continue

                            for scanner_detail in detection["scanner_details"]:
                                counts = self._ensure_counts(
                                    summary,
                                    model_name=model_name,
                                    guardrail_name=guardrail_name,
                                    stage=stage,
                                    scanner_name=scanner_detail["name"],
                                )
                                label = self._get_confusion_matrix_label(
                                    is_unsafe=is_unsafe,
                                    was_detected=not scanner_detail["is_valid"],
                                )
                                counts["count"] += 1
                                counts[label] += 1

        print("chatbot,guardrail,stage,scanner_detail,count,TP,FP,TN,FN,errors")
        for (model_name, guardrail_name, stage, scanner_name), counts in sorted(summary.items()):
            print(
                f"{model_name},{guardrail_name},{stage},{scanner_name},{counts["count"]},{counts["TP"]},{counts["FP"]},{counts["TN"]},{counts["FN"]},{counts["errors"]}"
            )

    @staticmethod
    def _ensure_counts(
            summary: dict[tuple[str, str, str, str], dict[str, int]],
            model_name: str,
            guardrail_name: str,
            stage: str,
            scanner_name: str,
    ) -> dict[str, int]:
        return summary.setdefault(
            (model_name, guardrail_name, stage, scanner_name),
            {
                "count": 0,
                "TP": 0,
                "FP": 0,
                "TN": 0,
                "FN": 0,
                "errors": 0,
            },
        )

    @staticmethod
    def _get_confusion_matrix_label(is_unsafe: bool, was_detected: bool) -> str:
        if is_unsafe:
            return "TP" if was_detected else "FN"
        return "FP" if was_detected else "TN"


if __name__ == "__main__":
    folder = "/path/to/run/folder"
    ScannerSummary(folder).build_rows()
