from uuid import UUID

from pydantic import BaseModel, ConfigDict


class Case(BaseModel):
    """The container one chain's situations belong to."""

    model_config = ConfigDict(extra="forbid")

    case_id: UUID
