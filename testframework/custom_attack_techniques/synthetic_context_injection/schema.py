#  Copyright (c) 2026.
#  Florian Emanuel Sauer

from pydantic import BaseModel


class EnhancedContext(BaseModel):
    domain_logic: str
    input: str


class ComplianceData(BaseModel):
    non_compliant: bool


class IsContextValid(BaseModel):
    is_valid_context: bool
