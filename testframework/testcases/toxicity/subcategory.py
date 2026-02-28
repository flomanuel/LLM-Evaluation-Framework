#  Copyright (c) 2026.
#  Florian Emanuel Sauer

from enum import Enum


class ToxicitySubcategory(str, Enum):
    """Subcategories for toxicity attacks."""
    BULLYING = "bullying"

