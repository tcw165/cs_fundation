from uuid import UUID

from pydantic import BaseModel


class Situation(BaseModel):
    situation_id: UUID
    desc: str
    is_root: bool


def require_single_root(situations: list[Situation]) -> None:
    root_count = sum(1 for situation in situations if situation.is_root)
    if root_count != 1:
        raise ValueError(f"expected one root, found {root_count}")
