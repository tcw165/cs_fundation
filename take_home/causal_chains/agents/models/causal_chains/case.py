from datetime import datetime
from typing import Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Case(BaseModel):
    """The container one chain's situations belong to."""

    model_config = ConfigDict(extra="forbid")

    case_id: UUID = Field(..., description="Id assigned when the case is created.")
    conversation_id: str = Field(..., description="Conversation this case belongs to.")
    created_timestamp: datetime = Field(..., description="When the case was created.")
    updated_timestamp: datetime = Field(..., description="When the case was last updated.")

    @model_validator(mode="after")
    def assigned_case_id(self) -> Self:
        if self.case_id.int == 0:
            raise ValueError("case id is missing")
        return self
