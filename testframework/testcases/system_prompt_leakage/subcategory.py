#  Copyright (c) 2026.
#  Florian Emanuel Sauer

from enum import Enum


class SystemPromptLeakageSubcategory(str, Enum):
    """Subcategories for system prompt leakage attacks."""
    INSTRUCTIONS = "instructions"
    GUARD_EXPOSURE = "guard-exposure"
    CUSTOM = "custom"
