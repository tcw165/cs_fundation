from uuid import UUID

from pydantic import BaseModel


class Situation(BaseModel):
    """Stored Neo4j node for one situation.

    This is the database row (:Situation {situation_id, desc, is_root}).
    Agents mutate a CausalChain, not this row.
    """

    situation_id: UUID
    desc: str
    is_root: bool


def require_single_root(situations: list[Situation]) -> None:
    root_count = sum(1 for situation in situations if situation.is_root)
    if root_count != 1:
        raise ValueError(f"expected one root, found {root_count}")
