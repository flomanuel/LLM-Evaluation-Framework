#  Copyright (c) 2026.
#  Florian Emanuel Sauer

from enum import Enum


class IndirectInstructionSubcategory(str, Enum):
    """Subcategories for indirect instruction attacks."""
    RAG_INJECTION = "rag-injection"
    DOCUMENT_EMBEDDED_INSTRUCTIONS = "document-embedded-instructions"

