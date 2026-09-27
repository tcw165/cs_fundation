from decimal import Decimal
from typing import Protocol, runtime_checkable
from uuid import UUID


@runtime_checkable
class GraphDb(Protocol):
    def p_query(self, destination_ids: list[UUID]) -> Decimal: ...

    def root_count(self) -> int: ...

    def broken_outgoing_sums(self) -> list[tuple[UUID, Decimal]]: ...
