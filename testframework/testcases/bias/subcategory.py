#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.


from enum import Enum


class BiasSubcategory(str, Enum):
    """Subcategories for bias attacks."""
    RACE = "race"
    GENDER = "gender"
    RELIGION = "religion"
    POLITICS = "politics"
