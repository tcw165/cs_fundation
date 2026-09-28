import asyncio
from decimal import Decimal
from uuid import UUID

from take_home.causal_chains.agents.models.causal_chains.input_variable import InputVariable
from take_home.causal_chains.agents.models.causal_chains.leads_to import LeadsTo
from take_home.causal_chains.agents.models.causal_chains.situation import Situation
from take_home.causal_chains.agents.stores.causal_chain_store.graph_causal_chain_store import (
    GraphCausalChainStore,
)
from take_home.causal_chains.agents.stores.causal_chain_store.protocol.protocol import (
    CausalChainStore,
)

NOW_ID = UUID("11111111-1111-4111-8111-111111111111")
DEAL_ID = UUID("22222222-2222-4222-8222-222222222222")


class _FakeGraphDb:
    def __init__(self) -> None:
        self.situations: list[tuple[UUID, str, bool]] = []
        self.links: list[tuple[UUID, UUID, Decimal, list[tuple[str, Decimal]]]] = []

    def merge_situation(
        self,
        situation_id: UUID,
        desc: str,
        is_root: bool,
    ) -> None:
        self.situations.append((situation_id, desc, is_root))

    def merge_leads_to(
        self,
        from_situation_id: UUID,
        to_situation_id: UUID,
        p: Decimal,
        inputs: list[tuple[str, Decimal]],
    ) -> None:
        self.links.append((from_situation_id, to_situation_id, p, inputs))


def test_graph_causal_chain_store_is_a_causal_chain_store():
    assert isinstance(GraphCausalChainStore(_FakeGraphDb()), CausalChainStore)


def test_add_situation_and_link_situations_record_calls():
    async def exercise():
        graph_db = _FakeGraphDb()
        store = GraphCausalChainStore(graph_db)
        now = Situation(situation_id=NOW_ID, version=1, desc="now", is_root=True)
        deal = Situation(situation_id=DEAL_ID, version=1, desc="deal", is_root=False)
        await store.add_situation(now)
        await store.link_situations(
            now,
            deal,
            LeadsTo(
                from_situation_id=NOW_ID,
                from_version=1,
                to_situation_id=DEAL_ID,
                to_version=1,
                inputs=[InputVariable(name="deal_odds", value=Decimal("0.08"))],
                p=Decimal("0.0800"),
            ),
        )
        return graph_db

    graph_db = asyncio.run(exercise())
    assert graph_db.situations == [
        (NOW_ID, "now", True),
        (NOW_ID, "now", True),
        (DEAL_ID, "deal", False),
    ]
    assert graph_db.links == [
        (NOW_ID, DEAL_ID, Decimal("0.0800"), [("deal_odds", Decimal("0.08"))]),
    ]
