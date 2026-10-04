from decimal import Decimal
from typing import Protocol, runtime_checkable
from uuid import UUID


@runtime_checkable
class GraphDb(Protocol):
    def p_query(self, destination_ids: list[UUID]) -> Decimal: ...

    def start_count(self) -> int: ...

    def broken_outgoing_sums(self) -> list[tuple[UUID, Decimal]]: ...

    def merge_case(
        self,
        case_id: UUID,
        conversation_id: str,
        created_timestamp: str,
        updated_timestamp: str,
    ) -> None: ...

    def get_case(self, case_id: UUID) -> tuple[UUID, str, str, str] | None: ...

    def merge_situation(
        self,
        situation_id: UUID,
        version: int,
        title: str,
        desc: str,
        remained_drivers: list[str],
        case_id: UUID,
        kind: str,
        potential_drivers: list[str],
        original_ask: str,
    ) -> None: ...

    def merge_leads_to(
        self,
        from_situation_id: UUID,
        from_version: int,
        to_situation_id: UUID,
        to_version: int,
        p: Decimal,
        inputs: list[tuple[str, str, float]],
    ) -> None: ...

    def list_situations(
        self,
    ) -> list[tuple[UUID, int, str, str, list[str], str, list[str], str, UUID]]: ...

    def list_leaf_situations(
        self,
        case_id: UUID,
        start_situation_id: UUID,
        start_version: int,
    ) -> list[tuple[UUID, int, str, str, list[str]]]: ...

    def reaches_terminal(
        self,
        case_id: UUID,
        start_situation_id: UUID,
        start_version: int,
        terminal_situation_id: UUID,
        terminal_version: int,
    ) -> bool: ...

    def lookup_chain_so_far(
        self,
        case_id: UUID,
        start_situation_id: UUID,
        start_version: int,
    ) -> tuple[
        tuple[UUID, int, str, str, list[str], list[str]],
        list[tuple[UUID, int, str, str, list[str]]],
        list[tuple[UUID, int, UUID, int, Decimal, list[tuple[str, str, float]]]],
    ] | None: ...

    def list_leads_to(
        self,
    ) -> list[tuple[UUID, int, UUID, int, Decimal, list[tuple[str, str, float]]]]: ...

    def clear(self) -> None: ...
