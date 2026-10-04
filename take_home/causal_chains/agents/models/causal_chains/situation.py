from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class Situation(BaseModel):
    """A stored situation. situation_id is assigned when it is saved. version starts at 1."""

    model_config = ConfigDict(extra="forbid")

    situation_id: UUID
    version: int
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


class StartSituation(Situation):
    """The saved present. potential_drivers are the drivers behind it."""

    potential_drivers: list[str] = Field(..., description="The drivers behind this present.")


class TerminalSituation(Situation):
    """The saved end, returned with the user's ask. Not the start."""

    original_ask: str


def require_single_start(situations: list[Situation]) -> None:
    start_count = sum(
        1 for situation in situations if isinstance(situation, StartSituation)
    )
    if start_count != 1:
        raise ValueError(f"expected one start, found {start_count}")
