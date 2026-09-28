import asyncio
from decimal import Decimal
from uuid import UUID

from take_home.causal_chains.agents.models.causal_chains.leads_to import LeadsTo
from take_home.causal_chains.agents.models.causal_chains.situation import Situation
from take_home.causal_chains.agents.stores.causal_chain_store.protocol.protocol import (
    CausalChainStore,
)

NOW_ID = UUID("11111111-1111-4111-8111-111111111111")
DEAL_ID = UUID("22222222-2222-4222-8222-222222222222")


class _Both:
    def __init__(self) -> None:
        self.situations: list[Situation] = []
        self.links: list[tuple[Situation, Situation, LeadsTo]] = []

    async def add_situation(
        self,
        situation: Situation,
    ) -> None:
        self.situations.append(situation)

    async def link_situations(
        self,
        from_situation: Situation,
        to_situation: Situation,
        link: LeadsTo,
    ) -> None:
        self.links.append((from_situation, to_situation, link))


class _AddOnly:
    async def add_situation(
        self,
        situation: Situation,
    ) -> None:
        return None


def test_causal_chain_store_requires_add_and_link():
    assert isinstance(_Both(), CausalChainStore)
    assert not isinstance(_AddOnly(), CausalChainStore)


def test_fake_records_a_situation_and_a_link():
    async def exercise():
        store = _Both()
        now = Situation(situation_id=NOW_ID, version=1, desc="now", is_root=True)
        deal = Situation(situation_id=DEAL_ID, version=1, desc="deal", is_root=False)
        link = LeadsTo(
            from_situation_id=NOW_ID,
            from_version=1,
            to_situation_id=DEAL_ID,
            to_version=1,
            p=Decimal("0.08"),
        )
        await store.add_situation(now)
        await store.link_situations(now, deal, link)
        return store, now, deal, link

    store, now, deal, link = asyncio.run(exercise())
    assert store.situations == [now]
    assert store.links == [(now, deal, link)]
