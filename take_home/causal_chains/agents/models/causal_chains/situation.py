from uuid import UUID

from pydantic import BaseModel, ConfigDict


class Situation(BaseModel):
    """A stored situation. situation_id is assigned when it is saved. version starts at 1."""

    model_config = ConfigDict(extra="forbid")

    situation_id: UUID
    version: int
    desc: str


class StartSituation(Situation):
    """The saved present. potential_factors are the drivers behind it."""

    potential_factors: list[str]


class TerminalSituation(Situation):
    """The saved end, returned with the user's ask. Not the start."""

    original_ask: str


def require_single_start(situations: list[Situation]) -> None:
    start_count = sum(
        1 for situation in situations if isinstance(situation, StartSituation)
    )
    if start_count != 1:
        raise ValueError(f"expected one start, found {start_count}")
