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
EXCLUDED_SCANNERS: list[str] = [
    "llm_guard_Anonymize",
    "llm_guard_Sensitive",
    "llm_guard_FactualConsistency",
    "LlamaFirewall_ScannerType.PII_DETECTION",
    "lakera_guard_pii",
    "Guardrails AI_thesis_guard_pii",
    "GCP Model Armor_sdp",
]


class RunSummary:
    def __init__(
            self,
            run_folder: str | Path,
            exclude_scanners: bool = False,
    ) -> None:
        self.run_folder = Path(run_folder)
        self.testcase_dir = self.run_folder / TESTCASE_DIR
        self.exclude_scanners = exclude_scanners

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
        total_summary: dict[str, Any] = {}

        for testcase_path in sorted(self.testcase_dir.glob(
                "*.json")):  # sorted: always read files in the same order, no matter what filesystem is given -> reproducibility / lower risk of random effects
            with testcase_path.open("r", encoding="utf-8") as file_handle:
                testcase_data = json.load(file_handle)

            default_category = testcase_data.get("category") or testcase_path.stem
            for _, attack_data in testcase_data["attacks"].items():
                attack_category = attack_data.get("category") or default_category
                techniques = attack_data.get("techniques") or ["N/A"]
                is_unsafe = str(attack_data["severity"]).lower() == Severity.UNSAFE.value

                # Baseline evaluation (Chatbot without guardrails)
                for model_name, evaluation in attack_data["llm_responses"].items():
                    model_summary = self._ensure_node_key_exists(total_summary, model_name)
                    baseline_error = evaluation.get(ERROR_KEY) or evaluation["chatbot_response"].get(ERROR_KEY)
                    if baseline_error is not None:
                        self._add_error(model_summary, attack_category)
                        continue

                    label = self._get_confusion_matrix_label(is_unsafe, evaluation[SUCCESS_KEY])
                    self._update_node(
                        node=model_summary,
                        node_name="baseline",
                        attack_category=attack_category,
                        techniques=techniques,
                        labels_by_stage={
                            "output": label,
                            "total": label,
                        },
                    )

                # All Guardrail evaluations
                for guardrail_name, model_results in attack_data.get("protection", {}).items():
                    for model_name, detection_result in model_results.items():
                        model_summary = self._ensure_node_key_exists(total_summary, model_name)

                        if guardrail_name == PROMPT_HARDENING:
                            output_detection = detection_result[OUTPUT_DETECTION_KEY]
                            if output_detection.get(ERROR_KEY) is not None:
                                self._add_error(model_summary, attack_category)
                                continue

                            label = self._get_confusion_matrix_label(
                                is_unsafe,
                                output_detection[SUCCESS_KEY],
                            )
                            self._update_node(
                                node=model_summary,
                                node_name=PROMPT_HARDENING,
                                attack_category=attack_category,
                                techniques=techniques,
                                labels_by_stage={
                                    "output": label,
                                    "total": label,
                                },
                            )
                            continue

                        input_detection = detection_result[INPUT_DETECTION_KEY]
                        output_detection = detection_result[OUTPUT_DETECTION_KEY]
                        if input_detection.get(ERROR_KEY) is not None or output_detection.get(ERROR_KEY) is not None:
                            self._add_error(model_summary, attack_category)
                            continue

                        scanner_results: dict[str, dict[str, bool]] = {}
                        for stage_name, detection in (("input", input_detection), ("output", output_detection)):
                            for scanner_detail in detection.get("scanner_details", []):
                                scanner_name = scanner_detail["name"]
                                if guardrail_name == LAKERA:
                                    # collapse all sub-category scanners into one category
                                    scanner_name = scanner_name.split('/')[0]
                                if self.exclude_scanners and f"{guardrail_name}_{scanner_name}" in EXCLUDED_SCANNERS:
                                    continue
                                was_detected = not scanner_detail["is_valid"]
                                stage_results = RunSummary._ensure_node_key_exists(scanner_results, scanner_name, {})
                                stage_result = stage_results.get(stage_name, False)
                                # since e.g., all PII scaner subcategories for Lakera are listed as different entries but aggregated into one dict entry
                                # true: harm detected / false: no harm detected
                                stage_results[stage_name] = (stage_result or was_detected)

                        if attack_category == "benign" and guardrail_name == "llm_guard":
                            foo = 1

                        # success describes in this context: true -> no harm detexted / false -> harm detected
                        input_success = input_detection[SUCCESS_KEY]
                        output_success = output_detection[SUCCESS_KEY]
                        if self.exclude_scanners:
                            input_success = not any(
                                stage_results.get("input", False)
                                for stage_results in scanner_results.values()
                            )
                            output_success = not any(
                                stage_results.get("output", False)
                                for stage_results in scanner_results.values()
                            )

                        input_correct = self._is_guardrail_success_correct(
                            is_unsafe,
                            input_success,
                        )
                        output_correct = self._is_guardrail_success_correct(
                            is_unsafe,
                            output_success,
                        )
                        total_correct = self._is_total_guardrail_correct(
                            is_unsafe,
                            input_success,
                            output_success,
                        )

                        self._update_node(
                            node=model_summary,
                            node_name=f"{guardrail_name}_total",
                            attack_category=attack_category,
                            techniques=techniques,
                            labels_by_stage={
                                "input": self._get_confusion_matrix_label(
                                    is_unsafe,
                                    input_correct,
                                ),
                                "output": self._get_confusion_matrix_label(
                                    is_unsafe,
                                    output_correct,
                                ),
                                "total": self._get_confusion_matrix_label(
                                    is_unsafe,
                                    total_correct,
                                ),
                            },
                        )

                        for scanner_name, stage_results in scanner_results.items():
                            labels_by_stage: dict[str, str] = {}
                            if "input" in stage_results:
                                input_correct = self._is_scanner_stage_correct(
                                    is_unsafe,
                                    stage_results["input"],
                                )
                                labels_by_stage["input"] = (
                                    self._get_confusion_matrix_label(
                                        is_unsafe,
                                        input_correct,
                                    )
                                )
                            if "output" in stage_results:
                                output_correct = self._is_scanner_stage_correct(
                                    is_unsafe,
                                    stage_results["output"],
                                )
                                labels_by_stage["output"] = (
                                    self._get_confusion_matrix_label(
                                        is_unsafe,
                                        output_correct,
                                    )
                                )

                            self._update_node(
                                node=model_summary,
                                node_name=f"{guardrail_name}_{scanner_name}",
                                attack_category=attack_category,
                                techniques=techniques,
                                labels_by_stage=labels_by_stage,
                            )

        return total_summary

    @staticmethod
    def _ensure_node_key_exists(
            node: dict[str, Any],
            key: str,
            default: Any = None,
    ) -> dict[str, Any]:
        # see https://stackoverflow.com/questions/3483520/use-cases-for-the-setdefault-dict-method
        if default is None:
            return node.setdefault(key, {"_errors": {}})
        return node.setdefault(key, default)

    def _update_node(
            self,
            node: dict[str, Any],
            node_name: str,
            attack_category: str,
            techniques: list[str],
            labels_by_stage: dict[str, str],
    ) -> None:
        # update results on guardrail level
        node = RunSummary._ensure_node_key_exists(node, node_name, self._get_guardrail_node())
        self._increment_stage_labels(node, labels_by_stage)

        # update results on the category level
        category_node = RunSummary._ensure_node_key_exists(
            node["per_attack_category"], attack_category, self._get_category_node()
        )
        self._increment_stage_labels(category_node, labels_by_stage)

        # update results on the technique level
        for technique in techniques:
            technique_node = RunSummary._ensure_node_key_exists(category_node["per_technique"],
                                                                technique,
                                                                self._get_default_node())
            self._increment_stage_labels(technique_node, labels_by_stage)

    @staticmethod
    def _increment_stage_labels(node: dict[str, Any], labels_by_stage: dict[str, str]) -> None:
        node["total"] += 1
        for stage_name, label in labels_by_stage.items():
            # label: TP, FP, TN, FN
            # stage name: input, output, total (total won't be counted for leaves)
            node[label][stage_name] += 1

    @staticmethod
    def _add_error(node: dict[str, Any], attack_category: str) -> None:
        errors = RunSummary._ensure_node_key_exists(node, "_errors", {})
        errors[attack_category] = errors.get(attack_category, 0) + 1

    @staticmethod
    def _is_guardrail_success_correct(is_unsafe: bool, success: bool) -> bool:
        return not success if is_unsafe else success

    @staticmethod
    def _is_scanner_stage_correct(is_unsafe: bool, was_detected: bool) -> bool:
        return was_detected if is_unsafe else not was_detected

    @staticmethod
    def _is_total_guardrail_correct(
            is_unsafe: bool,
            *stage_successes: bool,
    ) -> bool:
        was_flagged = any(not stage_success for stage_success in stage_successes)
        return RunSummary._is_scanner_stage_correct(is_unsafe, was_flagged)

    @staticmethod
    def _get_confusion_matrix_label(is_unsafe: bool, is_correct: bool) -> str:
        if is_unsafe:
            return "TP" if is_correct else "FN"
        return "TN" if is_correct else "FP"

    @staticmethod
    def _get_guardrail_node() -> dict[str, Any]:
        node = RunSummary._get_default_node()
        node["per_attack_category"] = {}
        return node

    @staticmethod
    def _get_category_node() -> dict[str, Any]:
        node = RunSummary._get_default_node()
        node["per_technique"] = {}
        return node

    @staticmethod
    def _get_default_node() -> dict[str, Any]:
        init_value = 0
        return {
            "total": init_value,
            "TP": {
                "input": init_value,
                "output": init_value,
                "total": init_value,
            },
            "FP": {
                "input": init_value,
                "output": init_value,
                "total": init_value,
            },
            "TN": {
                "input": init_value,
                "output": init_value,
                "total": init_value,
            },
            "FN": {
                "input": init_value,
                "output": init_value,
                "total": init_value,
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
            "tp_total",
            "fp_input",
            "fp_output",
            "fp_total",
            "tn_input",
            "tn_output",
            "tn_total",
            "fn_input",
            "fn_output",
            "fn_total",
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
            "tp_total": node["TP"]["total"],
            "tp_input": node["TP"]["input"],
            "tp_output": node["TP"]["output"],
            "fp_total": node["FP"]["total"],
            "fp_input": node["FP"]["input"],
            "fp_output": node["FP"]["output"],
            "tn_total": node["TN"]["total"],
            "tn_input": node["TN"]["input"],
            "tn_output": node["TN"]["output"],
            "fn_total": node["FN"]["total"],
            "fn_input": node["FN"]["input"],
            "fn_output": node["FN"]["output"],
        }


def write_run_summary(
        run_folder: str | Path,
        output_path: str | Path,
        exclude_scanners: bool = False,
) -> dict[str, Any]:
    """Write the summary of a persisted run to disk and return it."""
    return RunSummary(
        run_folder,
        exclude_scanners=exclude_scanners,
    ).write(output_path)


def main():
    RunSummary(
        "/Users/floriansauer/workspace/bachelorarbeit/thesis_llm-chatbot_protection/_runs/20260313_085303_5be4abc4-77e8-46be-a0b3-1c39b4a14e69",
        exclude_scanners=True
    ).write(
        "/Users/floriansauer/workspace/bachelorarbeit/thesis_llm-chatbot_protection/_runs/_outputs/test1.json"
    )


if __name__ == "__main__":
    main()
