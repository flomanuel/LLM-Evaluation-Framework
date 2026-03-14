from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from testframework.enums import Severity

SUCCESS_KEY = "success"
ERROR_KEY = "error"
INPUT_DETECTION_KEY = "input_detection"
OUTPUT_DETECTION_KEY = "output_detection"
TESTCASE_DIR = "testcase"
PROMPT_HARDENING = "prompt_hardening"
LAKERA = "lakera_guard"


class RunSummary:
    def __init__(self, run_folder: str | Path) -> None:
        self.run_folder = self._validate_run_folder(Path(run_folder))
        self.testcase_dir = self.run_folder / TESTCASE_DIR

    def write(self, output_path: str | Path) -> dict[str, Any]:
        """Trigger a summary build and write the result to the disk."""
        summary = self.build()
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(summary, indent=2, ensure_ascii=True) + "\n",
            encoding="utf-8",
        )
        self._write_model_csv_exports(summary=summary, output_path=output_path)
        return summary

    def build(self) -> dict[str, Any]:
        """Build the per-model summary from testcase JSON files in a run folder."""
        summary_by_model: dict[str, Any] = {}

        for testcase_path in sorted(self.testcase_dir.glob(
                "*.json")):  # sorted: always read files in the same order, no matter what filesystem is given -> reproducibility / lower risk of random effects
            with testcase_path.open("r", encoding="utf-8") as file_handle:
                testcase_data = json.load(file_handle)

            default_category = testcase_data.get("category") or testcase_path.stem
            for attack_id, attack_data in testcase_data["attacks"].items():
                attack_category = attack_data.get("category") or default_category
                techniques = attack_data.get("techniques") or ["N/A"]
                is_unsafe = str(attack_data["severity"]).lower() == Severity.UNSAFE.value

                for model_name, evaluation in attack_data["llm_responses"].items():
                    model_summary = self._ensure_key(summary_by_model, model_name)
                    baseline_error = evaluation.get(ERROR_KEY) or evaluation["chatbot_response"].get(ERROR_KEY)
                    if baseline_error is not None:
                        self._add_error(model_summary, attack_category)
                        continue

                    cm_field = self._get_confusion_matrix_field(is_unsafe, evaluation[SUCCESS_KEY])
                    self._update_node(
                        model_summary=model_summary,
                        node_name="baseline",
                        attack_category=attack_category,
                        techniques=techniques,
                        labels_by_stage={
                            "output": cm_field,
                            "io_together": cm_field,
                        },
                    )

                for guardrail_name, model_results in attack_data.get("protection", {}).items():
                    for model_name, detection_result in model_results.items():
                        model_summary = self._ensure_key(
                            summary_by_model,
                            model_name,
                        )

                        if guardrail_name == PROMPT_HARDENING:
                            output_detection = detection_result[OUTPUT_DETECTION_KEY]
                            if output_detection.get(ERROR_KEY) is not None:
                                self._add_error(model_summary, attack_category)
                                continue

                            cm_field = self._get_confusion_matrix_field(
                                is_unsafe,
                                output_detection[SUCCESS_KEY],
                            )
                            self._update_node(
                                model_summary=model_summary,
                                node_name=PROMPT_HARDENING,
                                attack_category=attack_category,
                                techniques=techniques,
                                labels_by_stage={
                                    "output": cm_field,
                                    "io_together": cm_field,
                                },
                            )
                            continue

                        input_detection = detection_result[INPUT_DETECTION_KEY]
                        output_detection = detection_result[OUTPUT_DETECTION_KEY]
                        if input_detection.get(ERROR_KEY) is not None or output_detection.get(ERROR_KEY) is not None:
                            self._add_error(model_summary, attack_category)
                            continue

                        input_correct = self._was_guardrail_success_correct(
                            is_unsafe,
                            input_detection[SUCCESS_KEY],
                        )
                        output_correct = self._was_guardrail_success_correct(
                            is_unsafe,
                            output_detection[SUCCESS_KEY],
                        )
                        self._update_node(
                            model_summary=model_summary,
                            node_name=f"{guardrail_name}_total",
                            attack_category=attack_category,
                            techniques=techniques,
                            labels_by_stage={
                                "input": self._get_confusion_matrix_field(
                                    is_unsafe,
                                    input_correct,
                                ),
                                "output": self._get_confusion_matrix_field(
                                    is_unsafe,
                                    output_correct,
                                ),
                                "io_together": self._get_confusion_matrix_field(
                                    is_unsafe,
                                    input_correct or output_correct, # todo: input_correct OR output_correct -> überall im Code!
                                ),
                            },
                        )

                        scanner_results: dict[str, dict[str, bool]] = {}
                        for stage_name, detection in (("input", input_detection), ("output", output_detection)):
                            for scanner_detail in detection.get("scanner_details", []):
                                scanner_name = scanner_detail["name"]
                                if guardrail_name == LAKERA:
                                    scanner_name = scanner_name.split('/')[0]
                                was_detected = not scanner_detail["is_valid"]
                                stage_results = scanner_results.setdefault(scanner_name, {})
                                stage_result = stage_results.get(stage_name, False)
                                stage_results[stage_name] = (
                                        stage_result or was_detected)  # since e.g., all PII scaner subcategories for Lakera are listed as different entries but aggregated into one dict entry

                        for scanner_name, stage_results in scanner_results.items():
                            labels_by_stage: dict[str, str] = {}
                            if "input" in stage_results:
                                labels_by_stage["input"] = (
                                    self._get_confusion_matrix_field(
                                        is_unsafe,
                                        stage_results["input"]
                                        if is_unsafe
                                        else not stage_results["input"],
                                    )
                                )
                            if "output" in stage_results:
                                labels_by_stage["output"] = (
                                    self._get_confusion_matrix_field(
                                        is_unsafe,
                                        stage_results["output"]
                                        if is_unsafe
                                        else not stage_results["output"],
                                    )
                                )
                            if "input" in stage_results and "output" in stage_results:
                                labels_by_stage["io_together"] = (
                                    self._get_confusion_matrix_field(
                                        is_unsafe,
                                        (
                                                stage_results["input"]
                                                and stage_results["output"]
                                        )
                                        if is_unsafe
                                        else not (
                                                stage_results["input"]
                                                or stage_results["output"]
                                        ),
                                    )
                                )

                            self._update_node(
                                model_summary=model_summary,
                                node_name=f"{guardrail_name}_{scanner_name}",
                                attack_category=attack_category,
                                techniques=techniques,
                                labels_by_stage=labels_by_stage,
                            )

        return summary_by_model

    @staticmethod
    def _validate_run_folder(run_folder: Path) -> Path:
        """Validate that the given folder and its path is a run folder/path."""
        if not run_folder.is_dir():
            raise FileNotFoundError(
                f"Run folder '{run_folder}' does not exist or is not a directory."
            )

        testcase_dir = run_folder / TESTCASE_DIR
        if not testcase_dir.is_dir():
            raise FileNotFoundError(
                f"Run folder '{run_folder}' does not contain a testcase directory."
            )

        return run_folder

    @staticmethod
    def _ensure_key(
            summary_by_model: dict[str, Any],
            model_name: str,
    ) -> dict[str, Any]:
        return summary_by_model.setdefault(model_name, {"_errors": {}})

    def _update_node(
            self,
            model_summary: dict[str, Any],
            node_name: str,
            attack_category: str,
            techniques: list[str],
            labels_by_stage: dict[str, str],
    ) -> None:
        node = model_summary.setdefault(node_name, self._new_root_node())
        self._apply_labels(node, labels_by_stage)

        category_node = node["per_attack_category"].setdefault(
            attack_category,
            self._new_category_node(),
        )
        self._apply_labels(category_node, labels_by_stage)

        for technique in techniques:
            technique_node = category_node["per_technique"].setdefault(
                technique,
                self._get_new_node(),
            )
            self._apply_labels(technique_node, labels_by_stage)

    @staticmethod
    def _apply_labels(node: dict[str, Any], labels_by_stage: dict[str, str]) -> None:
        node["total"] += 1
        for stage_name, label in labels_by_stage.items():
            node[label][stage_name] += 1

    @staticmethod
    def _add_error(model_summary: dict[str, Any], attack_category: str) -> None:
        errors = model_summary.setdefault("_errors", {})
        errors[attack_category] = errors.get(attack_category, 0) + 1

    @staticmethod
    def _was_guardrail_success_correct(is_unsafe: bool, success: bool) -> bool:
        return not success if is_unsafe else success

    @staticmethod
    def _get_confusion_matrix_field(is_unsafe: bool, was_correct: bool) -> str:
        if is_unsafe:
            return "TP" if was_correct else "FN"
        return "TN" if was_correct else "FP"

    @staticmethod
    def _new_root_node() -> dict[str, Any]:
        node = RunSummary._get_new_node()
        node["per_attack_category"] = {}
        return node

    @staticmethod
    def _new_category_node() -> dict[str, Any]:
        node = RunSummary._get_new_node()
        node["per_technique"] = {}
        return node

    @staticmethod
    def _get_new_node() -> dict[str, Any]:
        init_value = 0
        return {
            "total": init_value,
            "TP": {
                "input": init_value,
                "output": init_value,
                "io_together": init_value,
            },
            "FP": {
                "input": init_value,
                "output": init_value,
                "io_together": init_value,
            },
            "TN": {
                "input": init_value,
                "output": init_value,
                "io_together": init_value,
            },
            "FN": {
                "input": init_value,
                "output": init_value,
                "io_together": init_value,
            }
        }

    def _write_model_csv_exports(
            self,
            summary: dict[str, Any],
            output_path: Path,
    ) -> None:
        exports_dir = output_path.parent / output_path.stem
        exports_dir.mkdir(parents=True, exist_ok=True)

        for model_name, model_summary in summary.items():
            model_dir = exports_dir / model_name.strip().replace("/", "_")
            model_dir.mkdir(parents=True, exist_ok=True)
            self._write_summary_csv(
                model_summary=model_summary,
                output_path=model_dir / "summary.csv",
            )

    def _write_summary_csv(
            self,
            model_summary: dict[str, Any],
            output_path: Path,
    ) -> None:
        fieldnames = [
            "node",
            "scope",
            "attack_category",
            "technique",
            "total",
            "tp_input",
            "tp_output",
            "tp_io_together",
            "fp_input",
            "fp_output",
            "fp_io_together",
            "tn_input",
            "tn_output",
            "tn_io_together",
            "fn_input",
            "fn_output",
            "fn_io_together",
        ]
        rows = self._build_summary_csv_rows(model_summary)
        with output_path.open("w", encoding="utf-8", newline="") as file_handle:
            writer = csv.DictWriter(file_handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    def _build_summary_csv_rows(self, model_summary: dict[str, Any]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []

        for node_name, node in model_summary.items():
            if node_name == "_errors":
                continue

            rows.append(
                self._summary_csv_row(
                    node_name=node_name,
                    scope="overall",
                    attack_category="",
                    technique="",
                    node=node,
                )
            )

            for attack_category, category_node in node["per_attack_category"].items():
                rows.append(
                    self._summary_csv_row(
                        node_name=node_name,
                        scope="attack_category",
                        attack_category=attack_category,
                        technique="",
                        node=category_node,
                    )
                )

                for technique, technique_node in category_node["per_technique"].items():
                    rows.append(
                        self._summary_csv_row(
                            node_name=node_name,
                            scope="technique",
                            attack_category=attack_category,
                            technique=technique,
                            node=technique_node,
                        )
                    )

        return rows

    @staticmethod
    def _summary_csv_row(
            node_name: str,
            scope: str,
            attack_category: str,
            technique: str,
            node: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "node": node_name,
            "scope": scope,
            "attack_category": attack_category,
            "technique": technique,
            "total": node["total"],
            "tp_io_together": node["TP"]["io_together"],
            "tp_input": node["TP"]["input"],
            "tp_output": node["TP"]["output"],
            "fp_io_together": node["FP"]["io_together"],
            "fp_input": node["FP"]["input"],
            "fp_output": node["FP"]["output"],
            "tn_io_together": node["TN"]["io_together"],
            "tn_input": node["TN"]["input"],
            "tn_output": node["TN"]["output"],
            "fn_io_together": node["FN"]["io_together"],
            "fn_input": node["FN"]["input"],
            "fn_output": node["FN"]["output"],
        }


def write_run_summary(
        run_folder: str | Path,
        output_path: str | Path,
) -> dict[str, Any]:
    """Write the summary of a persisted run to disk and return it."""
    return RunSummary(run_folder).write(output_path)

# def main():
#     summary = RunSummary(
#         "/Users/floriansauer/workspace/bachelorarbeit/thesis_llm-chatbot_protection/_runs/20260313_085303_5be4abc4-77e8-46be-a0b3-1c39b4a14e69"
#     ).write(
#         "/Users/floriansauer/workspace/bachelorarbeit/thesis_llm-chatbot_protection/_runs/_outputs/test1.json"
#     )
#
#
# if __name__ == "__main__":
#     main()
