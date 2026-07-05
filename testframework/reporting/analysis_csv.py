#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

"""Reconstruct the historical per-model `summary.csv` exports from stored SummaryRow DTOs.

Mirrors ``RunSummary._build_summary_csv_rows`` / ``_write_model_csv_exports`` in reverse:
those build CSV rows from an in-memory summary dict and write one file per model to disk;
here we start from the already-persisted ``SummaryRow`` rows (``node`` stored as
``"<model_name>/<node_name>"``) and regroup them back into one CSV per model, in-memory.
"""

import csv
import io
import zipfile
from collections.abc import Iterable
from typing import Final

from testframework.models import AnalysisRunResult, SummaryRow

__all__ = ["build_analyses_zip", "group_rows_by_model", "sanitize_model_name", "write_summary_csv"]

FIELDNAMES: Final = ["node", "scope", "attack_category", "technique", "count", "tp", "fp", "tn", "fn"]

# Folder name per consider_chatbot_success variant within the exported ZIP.
_VARIANT_FOLDER_NAMES: Final = {
    True: "consider_model_alignment",
    False: "without_model_alignment",
}


def sanitize_model_name(model_name: str) -> str:
    """Match the historical `_output` sanitization: strip + replace '/' with '_'."""
    return model_name.strip().replace("/", "_")


def _split_node(node: str) -> tuple[str, str]:
    """Split the stored 'model_name/node_name' on the first '/'."""
    model_name, _, node_name = node.partition("/")
    return model_name, node_name


def group_rows_by_model(rows: Iterable[SummaryRow]) -> dict[str, list[dict[str, object]]]:
    """Group summary rows by model_name, restoring `node` to just the node-name part."""
    grouped: dict[str, list[dict[str, object]]] = {}
    for row in rows:
        model_name, node_name = _split_node(row.node)
        grouped.setdefault(model_name, []).append({
            "node": node_name,
            "scope": row.scope,
            "attack_category": row.attack_category,
            "technique": row.technique,
            "count": row.count,
            "tp": row.tp,
            "fp": row.fp,
            "tn": row.tn,
            "fn": row.fn,
        })
    return grouped


def write_summary_csv(rows: list[dict[str, object]]) -> str:
    """Render rows to a CSV string using the historical fieldnames/order."""
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=FIELDNAMES)
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def build_analyses_zip(analyses: Iterable[AnalysisRunResult]) -> bytes:
    """Build the `analyses_<run_id>.zip` content for the given (already-filtered) analyses.

    Layout: `<variant_folder>/<model_name>/summary.csv`, one variant folder per analysis.
    """
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for analysis in analyses:
            folder = _VARIANT_FOLDER_NAMES[analysis.consider_chatbot_success]
            for model_name, rows in group_rows_by_model(analysis.summary_rows).items():
                safe_model = sanitize_model_name(model_name)
                zip_file.writestr(f"{folder}/{safe_model}/summary.csv", write_summary_csv(rows))
    return buffer.getvalue()
