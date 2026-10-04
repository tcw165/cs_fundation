from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class Situation(BaseModel):
    """A stored situation. situation_id is assigned when it is saved. version starts at 1."""

    model_config = ConfigDict(extra="forbid")

    situation_id: UUID
    version: int
    kind: Literal["start", "situation", "terminal"] = Field(
        ...,
        description="start, situation, or terminal.",
    )
    created_timestamp: datetime = Field(
        ...,
        description="When this situation was saved.",
    )
    title: str = Field(..., description="A short and readable description within 100 words.")
    desc: str = Field(
        ...,
        description="Detailed statements in this situation (much longer than title).",
    )
    remained_drivers: list[str] = Field(
        ...,
        description="Drivers from the start situation still left to change.",
    )


def require_single_start(situations: list[Situation]) -> None:
    start_count = sum(1 for situation in situations if situation.kind == "start")
    if start_count != 1:
        raise ValueError(f"expected one start, found {start_count}")
