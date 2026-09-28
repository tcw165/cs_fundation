import asyncio
from decimal import Decimal
from uuid import UUID

from take_home.causal_chains.agents.models.messaging.causal_chain import CausalChain
from take_home.causal_chains.agents.models.causal_chains.input_variable import InputVariable
from take_home.causal_chains.agents.models.causal_chains.leads_to import LeadsTo
from take_home.causal_chains.agents.models.causal_chains.situation import (
    Situation,
    StartSituation,
)
from take_home.causal_chains.agents.stores.causal_chain_store.graph_causal_chain_store import (
    GraphCausalChainStore,
)
from take_home.causal_chains.agents.stores.causal_chain_store.protocol.protocol import (
    CausalChainStore,
)

NOW_ID = UUID("11111111-1111-4111-8111-111111111111")
DEAL_ID = UUID("22222222-2222-4222-8222-222222222222")
OTHER_ROOT_ID = UUID("33333333-3333-4333-8333-333333333333")
LEAF_ID = UUID("44444444-4444-4444-8444-444444444444")


class _FakeGraphDb:
    def __init__(self) -> None:
        self.situation_calls: list[tuple[UUID, int, str, bool]] = []
        self.link_calls: list[
            tuple[UUID, int, UUID, int, Decimal, list[tuple[str, Decimal]]]
        ] = []
        self._situations: dict[tuple[UUID, int], tuple[UUID, int, str, bool]] = {}
        self._links: list[
            tuple[UUID, int, UUID, int, Decimal, list[tuple[str, Decimal]]]
        ] = []

    def merge_situation(
        self,
        situation_id: UUID,
        version: int,
        desc: str,
        is_root: bool,
    ) -> None:
        row = (situation_id, version, desc, is_root)
        self.situation_calls.append(row)
        self._situations[(situation_id, version)] = row

    def merge_leads_to(
        self,
        from_situation_id: UUID,
        from_version: int,
        to_situation_id: UUID,
        to_version: int,
        p: Decimal,
        inputs: list[tuple[str, Decimal]],
    ) -> None:
        row = (
            from_situation_id,
            from_version,
            to_situation_id,
            to_version,
            p,
            inputs,
        )
        self.link_calls.append(row)
        self._links.append(row)

    def list_situations(
        self,
    ) -> list[tuple[UUID, int, str, bool]]:
        return list(self._situations.values())

    def list_leads_to(
        self,
    ) -> list[tuple[UUID, int, UUID, int, Decimal, list[tuple[str, Decimal]]]]:
        return list(self._links)


def test_graph_causal_chain_store_is_a_causal_chain_store():
    assert isinstance(GraphCausalChainStore(_FakeGraphDb()), CausalChainStore)


def test_add_situation_and_link_situations_record_calls():
    async def exercise():
        graph_db = _FakeGraphDb()
        store = GraphCausalChainStore(graph_db)
        now = StartSituation(
            situation_id=NOW_ID,
            version=1,
            desc="now",
            potential_factors=[],
        )
        deal = Situation(situation_id=DEAL_ID, version=1, desc="deal")
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
    assert graph_db.situation_calls == [
        (NOW_ID, 1, "now", True),
        (NOW_ID, 1, "now", True),
        (DEAL_ID, 1, "deal", False),
    ]
    assert graph_db.link_calls == [
        (
            NOW_ID,
            1,
            DEAL_ID,
            1,
            Decimal("0.0800"),
            [("deal_odds", Decimal("0.08"))],
        ),
    ]


def _link(
    from_situation: Situation,
    to_situation: Situation,
) -> LeadsTo:
    return LeadsTo(
        from_situation_id=from_situation.situation_id,
        from_version=from_situation.version,
        to_situation_id=to_situation.situation_id,
        to_version=to_situation.version,
        p=Decimal("1"),
    )


def test_get_chains_returns_one_chain_per_root():
    async def exercise():
        graph_db = _FakeGraphDb()
        store = GraphCausalChainStore(graph_db)
        now = StartSituation(
            situation_id=NOW_ID,
            version=1,
            desc="now",
            potential_factors=[],
        )
        other = StartSituation(
            situation_id=OTHER_ROOT_ID,
            version=1,
            desc="other",
            potential_factors=[],
        )
        deal = Situation(situation_id=DEAL_ID, version=1, desc="deal")
        leaf = Situation(situation_id=LEAF_ID, version=1, desc="leaf")
        orphan = Situation(
            situation_id=UUID("55555555-5555-4555-8555-555555555555"),
            version=1,
            desc="orphan",
        )
        await store.add_situation(now)
        await store.add_situation(other)
        await store.add_situation(orphan)
        await store.link_situations(now, deal, _link(now, deal))
        await store.link_situations(deal, leaf, _link(deal, leaf))
        await store.link_situations(other, deal, _link(other, deal))
        await store.link_situations(now, other, _link(now, other))
        return await store.get_chains()

    chains = asyncio.run(exercise())
    now = StartSituation(
        situation_id=NOW_ID,
        version=1,
        desc="now",
        potential_factors=[],
    )
    other = StartSituation(
        situation_id=OTHER_ROOT_ID,
        version=1,
        desc="other",
        potential_factors=[],
    )
    deal = Situation(situation_id=DEAL_ID, version=1, desc="deal")
    leaf = Situation(situation_id=LEAF_ID, version=1, desc="leaf")
    assert chains == [
        CausalChain(
            situations=[now, deal, leaf],
            links=[_link(now, deal), _link(deal, leaf)],
        ),
        CausalChain(
            situations=[other, deal, leaf],
            links=[_link(other, deal), _link(deal, leaf)],
        ),
    ]


def test_get_chains_returns_empty_when_the_graph_is_empty():
    async def exercise():
        return await GraphCausalChainStore(_FakeGraphDb()).get_chains()

    assert asyncio.run(exercise()) == []
