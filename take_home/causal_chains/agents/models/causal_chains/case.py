from typing import Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, model_validator


class Case(BaseModel):
    """The container one chain's situations belong to."""

    model_config = ConfigDict(extra="forbid")

    case_id: UUID
    conversation_id: str

    @model_validator(mode="after")
    def assigned_case_id(self) -> Self:
        if self.case_id.int == 0:
            raise ValueError("case id is missing")
        return self
