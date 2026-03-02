#  Copyright (c) 2026.
#  Florian Emanuel Sauer

#  Copyright (c) 2026.
#  Florian Emanuel Sauer

from enum import Enum


class BiasSubcategory(str, Enum):
    """Subcategories for bias attacks."""
    RACE = "race"
    GENDER = "gender"
    RELIGION = "religion"
    POLITICS = "politics"
