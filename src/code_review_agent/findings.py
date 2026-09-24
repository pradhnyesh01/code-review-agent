from typing import Literal

from pydantic import BaseModel

Category = Literal["style", "test-coverage"]
Severity = Literal["nit", "warning", "blocker"]


class Finding(BaseModel):
    file: str
    line: int
    comment: str
    category: Category
    severity: Severity
