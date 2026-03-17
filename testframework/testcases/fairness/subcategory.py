#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.


from enum import Enum


class FairnessSubcategory(str, Enum):
    """Subcategories for fairness attacks."""
    BANKING = "banking"
    DISTRIBUTIVE_FAIRNESS = "distributive-fairness"
    PROCEDURAL_FAIRNESS = "procedural-fairness"
