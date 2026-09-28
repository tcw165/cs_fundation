from uuid import UUID

from pydantic import BaseModel, ConfigDict


class Situation(BaseModel):
    """A stored situation. situation_id is assigned when it is saved. version starts at 1."""

    model_config = ConfigDict(extra="forbid")

    situation_id: UUID
    version: int
    desc: str
    is_root: bool


class TerminalSituation(Situation):
    """The saved end, returned with the user's ask. Not the root."""

    original_ask: str


def require_single_root(situations: list[Situation]) -> None:
    root_count = sum(1 for situation in situations if situation.is_root)
    if root_count != 1:
        raise ValueError(f"expected one root, found {root_count}")
