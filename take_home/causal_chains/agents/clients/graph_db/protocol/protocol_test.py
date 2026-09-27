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
        desc: str,
        is_root: bool,
    ) -> None:
        return None

    def merge_leads_to(
        self,
        from_situation_id: UUID,
        to_situation_id: UUID,
        p: Decimal,
    ) -> None:
        return None


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
