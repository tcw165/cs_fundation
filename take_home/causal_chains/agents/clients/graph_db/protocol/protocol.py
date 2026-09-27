from decimal import Decimal
from typing import Protocol, runtime_checkable
from uuid import UUID


@runtime_checkable
class GraphDb(Protocol):
    def p_query(self, destination_ids: list[UUID]) -> Decimal: ...

    def root_count(self) -> int: ...

    def broken_outgoing_sums(self) -> list[tuple[UUID, Decimal]]: ...

    def merge_situation(
        self,
        situation_id: UUID,
        desc: str,
        is_root: bool,
    ) -> None: ...

    def merge_leads_to(
        self,
        from_situation_id: UUID,
        to_situation_id: UUID,
        p: Decimal,
    ) -> None: ...
