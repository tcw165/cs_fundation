from decimal import Decimal
from uuid import UUID

from take_home.causal_chains.agents.clients.graph_db.protocol.protocol import GraphDb


class _Both:
    def p_query(
        self,
        destination_ids: list[UUID],
    ) -> Decimal:
        return Decimal("0")

    def root_count(self) -> int:
        return 0

    def broken_outgoing_sums(self) -> list[tuple[UUID, Decimal]]:
        return []

    def merge_situation(
        self,
        situation_id: UUID,
        version: int,
        desc: str,
        is_root: bool,
        is_end: bool,
    ) -> None:
        return None

    def merge_leads_to(
        self,
        from_situation_id: UUID,
        from_version: int,
        to_situation_id: UUID,
        to_version: int,
        p: Decimal,
        inputs: list[tuple[str, Decimal]],
    ) -> None:
        return None

    def list_situations(
        self,
    ) -> list[tuple[UUID, int, str, bool, bool]]:
        return []

    def list_leads_to(
        self,
    ) -> list[tuple[UUID, int, UUID, int, Decimal, list[tuple[str, Decimal]]]]:
        return []


class _ReadsOnly:
    def p_query(
        self,
        destination_ids: list[UUID],
    ) -> Decimal:
        return Decimal("0")

    def root_count(self) -> int:
        return 0

    def broken_outgoing_sums(self) -> list[tuple[UUID, Decimal]]:
        return []


def test_graph_db_requires_reads_and_writes():
    assert isinstance(_Both(), GraphDb)
    assert not isinstance(_ReadsOnly(), GraphDb)
