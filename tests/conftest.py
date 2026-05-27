#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

import sys
from unittest.mock import MagicMock

# 'guardrails' was removed from project dependencies but is still imported in
# testframework/guardrails/guardrails_ai/guardrails_ai.py.
# Insert a stub before any test collection to prevent ModuleNotFoundError.
if "guardrails" not in sys.modules:
    sys.modules["guardrails"] = MagicMock()
