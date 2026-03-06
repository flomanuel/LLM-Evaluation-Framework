#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.



from enum import Enum


class EthicsSubcategory(str, Enum):
    """Subcategories for ethics attacks."""
    BANKING = "banking"
    HARM_PREVENTION = "harm-prevention"
    MORAL_INTEGRITY = "moral-integrity"
