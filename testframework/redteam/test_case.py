#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.


from dataclasses import dataclass, field
from typing import Any


@dataclass
class RTTestCase:
    """
    Project-owned red-team test case contract.

    This mirrors the currently used DeepTeam RTTestCase fields so callers can
    migrate incrementally without changing behavior.
    """

    vulnerability: str
    input: str
    vulnerability_type: Any = None
    actual_output: str | None = None
    metadata: dict[str, Any] | None = field(default_factory=dict)
    retrieval_context: Any = None
