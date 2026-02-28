#  Copyright (c) 2026.
#  Florian Emanuel Sauer

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Mapping

from testframework.enums import Severity


@dataclass(frozen=True)
class CSVAttackRow:
    prompt: str
    severity: str
    categories: list[str]
    tool_check: bool
    tool_check_condition: str | None
    remote_attack_generation: str | None
    document_path: str | None

    @classmethod
    def from_csv_row(cls, row: Mapping[str, str | None]) -> "CSVAttackRow":
        categories_raw = row.get("category") or ""
        tool_check_raw = (row.get("tool_check") or "").strip().lower()
        if tool_check_raw not in {"true", "false"}:
            raise ValueError(
                f"Unsupported tool_check value in CSV row: {row.get('tool_check')}"
            )

        return cls(
            prompt=row.get("prompt") or "",
            severity=(row.get("severity") or "").strip(),
            categories=[
                category.strip()
                for category in categories_raw.split(";")
                if category.strip()
            ],
            tool_check=tool_check_raw == "true",
            tool_check_condition=cls._normalize_optional(
                row.get("tool_check_condition"),
                false_as_none=True,
            ),
            remote_attack_generation=cls._normalize_optional(
                row.get("remote_attack_generation")
            ),
            document_path=cls._normalize_optional(row.get("document")),
        )

    @staticmethod
    def _normalize_optional(
            value: str | None,
            false_as_none: bool = False,
    ) -> str | None:
        if value is None:
            return None

        normalized = value.strip()
        if not normalized:
            return None
        if false_as_none and normalized.lower() == "false":
            return None
        return normalized

    def matches_filters(
            self,
            categories: list[str],
            severity: Severity,
    ) -> bool:
        if self.severity != severity.value:
            return False
        if not categories:
            return True
        return any(category in self.categories for category in categories)

    def build_attack_metadata(self) -> dict[str, Any] | None:
        if not self.tool_check:
            return None

        metadata: dict[str, Any] = {
            "tool_check": True,
            "tool_check_mode": "prompt_injected_code",
        }
        if self.tool_check_condition is not None:
            metadata["tool_check_condition"] = self.tool_check_condition
        return metadata


class CSVLoader():
    CSV_DOCUMENTS_FOLDER: Path = Path(__file__).resolve().parents[2] / "_prompt_files"

    def __init__(self) -> None:
        pass

    @staticmethod
    def load_prompts_from_csv(
            file_path: str,
            categories: List[str] | None = None,
            severity: Severity = Severity.UNSAFE,
    ) -> List[CSVAttackRow]:
        """Loads prompts from a csv that follows the format 'prompt,severity,category,tool_check,tool_check_condition,remote_attack_generation,document'
        where the column category contains a string that concatenates applicable categories via ; as a delimiter.

        Args:
            file_path (str): relative file path to the CSV-file (root is `<project_root>/_prompt_files`)
            categories (List[str]): categories to filter the prompts
            severity (Severity): whether the prompt should return harmful or benign prompts. Defaults to harmful prompts.

        Returns:
            List[CSVAttackRow]: Filtered CSV attack rows with normalized types.
        """
        prompts: List[CSVAttackRow] = []
        effective_categories = categories or []
        path = CSVLoader._build_full_path(file_path)
        with open(path, encoding="UTF-8") as csvfile:
            csv_file = csv.DictReader(csvfile)
            for row in csv_file:
                attack_row = CSVAttackRow.from_csv_row(row)
                if attack_row.matches_filters(effective_categories, severity):
                    prompts.append(attack_row)
        return prompts

    @staticmethod
    def _build_full_path(file_path: str):
        if not file_path.lower().endswith(".csv"):
            raise ValueError(f"Only CSV files are supported, got: {file_path}")

        full_path = (CSVLoader.CSV_DOCUMENTS_FOLDER / file_path).resolve()

        try:
            full_path.relative_to(CSVLoader.CSV_DOCUMENTS_FOLDER.resolve())
        except ValueError:
            raise ValueError(
                f"Path traversal attempt detected: {file_path} resolves outside "
                f"the allowed folder"
            )

        if not full_path.exists():
            raise FileNotFoundError(f"Document not found: {file_path}")

        if not full_path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")
        return full_path
