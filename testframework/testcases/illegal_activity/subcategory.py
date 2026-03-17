#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.


from enum import Enum


class IllegalActivitySubcategory(str, Enum):
    """Subcategories for illegal activity attacks."""
    WEAPONS = "weapons"
    CHILD_EXPLOITATION = "child-exploitation"
    ILLEGAL_DRUGS = "illegal-drugs"
    VIOLENT_CRIME = "violent-crime"
    NONVIOLENT_CRIME = "nonviolent-crime"
    SEX_CRIME = "sex-crime"
    CYBERCRIME = "cyber-crime"
