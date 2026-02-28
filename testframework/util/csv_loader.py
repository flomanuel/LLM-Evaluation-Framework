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
            document_path=row.get("document"),
        )

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

    def build_attack_metadata(self, is_rag: bool = True) -> dict[str, Any]:
        metadata: dict[str, Any] = {"file_path": self.document_path, "is_rag": is_rag}
        if not self.tool_check:
            return metadata
        metadata["tool_check"] = True
        metadata["tool_check_mode"] = "prompt_injected_code"
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
        """
        Loads prompts from a CSV file.
        :param file_path:
        :param categories:
        :param severity:
        :return:
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
