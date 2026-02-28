#  Copyright (c) 2026.
#  Florian Emanuel Sauer

from enum import Enum


class EthicsSubcategory(str, Enum):
    """Subcategories for ethics attacks."""
    BANKING = "banking"
    HARM_PREVENTION = "harm-prevention"
    MORAL_INTEGRITY = "moral-integrity"
