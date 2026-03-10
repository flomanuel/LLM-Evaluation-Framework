#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.


from enum import Enum


class ToxicitySubcategory(str, Enum):
    """Subcategories for toxicity attacks."""
    BULLYING = "bullying"
    INSULTS = "insults"
    PROFANITY = "profanity"
    THREATS = "threats"
    MOCKERY = "mockery"
