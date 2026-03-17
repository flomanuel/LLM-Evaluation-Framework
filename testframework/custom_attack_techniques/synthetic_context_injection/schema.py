#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.


from pydantic import BaseModel


class EnhancedContext(BaseModel):
    domain_logic: str
    input: str


class ComplianceData(BaseModel):
    non_compliant: bool


class IsContextValid(BaseModel):
    is_valid_context: bool
