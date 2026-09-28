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
        version: int,
        desc: str,
        is_root: bool,
    ) -> None: ...

    def merge_leads_to(
        self,
        from_situation_id: UUID,
        from_version: int,
        to_situation_id: UUID,
        to_version: int,
        p: Decimal,
        inputs: list[tuple[str, Decimal]],
    ) -> None: ...

    def list_situations(
        self,
    ) -> list[tuple[UUID, int, str, bool]]: ...

    def list_leads_to(
        self,
    ) -> list[tuple[UUID, int, UUID, int, Decimal, list[tuple[str, Decimal]]]]: ...
