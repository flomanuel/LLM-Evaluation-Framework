import csv
from pathlib import Path
from typing import List

from testframework.enums import Severity

class CSVLoader():

    CSV_DOCUMENTS_FOLDER: Path = Path(__file__).resolve().parents[2] / "_prompt_files"
    
    def __init__(self) -> None:
        pass

    @staticmethod
    def load_prompts_from_csv(file_path: str, categories: List[str] = [], severity: Severity = Severity.UNSAFE) -> List[str]: 
        """Loads prompts from a csv that followd the format 'prompt,severity,category,tool_check,tool_check_condition,remote_atttack_generation,document'
        where the column category contains a string that concatenates applicable categories via ; as a delimiter.

        Args:
            file_path (str): relative file path to the CSV-file (root is `<project_root>/_propmt_files`)
            categories (str): categories to filter the prompts
            severity (str): wehther the prompt should return harmful or benign prompts. Defaults to harmful prompts.
        """
        prompts: List[str] = []
        path = CSVLoader._build_full_path(file_path)
        with open(path) as csvfile:
            csv_file = csv.reader(csvfile, quotechar='#')
            for row in csv_file:
                row_prompt = row[0]
                row_severity = row[1]
                row_categories = row[2]
                if row_severity == severity.value and any(category in row_categories for category in categories):
                    prompts.append(row_prompt)
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
