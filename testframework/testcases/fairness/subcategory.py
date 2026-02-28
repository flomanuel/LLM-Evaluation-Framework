#  Copyright (c) 2026.
#  Florian Emanuel Sauer

from enum import Enum


class FairnessSubcategory(str, Enum):
    """Subcategories for fairness attacks."""
    BANKING = "banking"
    DISTRIBUTIVE_FAIRNESS = "distributive-fairness"
    PROCEDURAL_FAIRNESS = "procedural-fairness"

