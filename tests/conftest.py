import sys
from unittest.mock import MagicMock

# 'guardrails' was removed from project dependencies but is still imported in
# testframework/guardrails/guardrails_ai/guardrails_ai.py.
# Insert a stub before any test collection to prevent ModuleNotFoundError.
if "guardrails" not in sys.modules:
    sys.modules["guardrails"] = MagicMock()
