#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.



from enum import Enum


class IndirectInstructionSubcategory(str, Enum):
    """Subcategories for indirect instruction attacks."""
    DOCUMENT_EMBEDDED_INSTRUCTIONS = "document-embedded-instructions"
