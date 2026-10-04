import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from take_home.causal_chains.agents.models.messaging.causal_chain import CausalChain
from take_home.causal_chains.agents.models.causal_chains.case import Case
from take_home.causal_chains.agents.models.causal_chains.chain_so_far import ChainSoFar
from take_home.causal_chains.agents.models.causal_chains.leads_to import LeadsTo
from take_home.causal_chains.agents.models.causal_chains.situation import (
    Situation,
    StartSituation,
    TerminalSituation,
)
from take_home.causal_chains.agents.stores.causal_chain_store.protocol.protocol import (
    CausalChainStore,
)

NOW_ID = UUID("11111111-1111-4111-8111-111111111111")
DEAL_ID = UUID("22222222-2222-4222-8222-222222222222")
CASE_ID = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
CREATED = datetime(2026, 10, 1, tzinfo=timezone.utc)


class _Both:
    def __init__(self) -> None:
        self.cases: list[Case] = []
        self.situations: list[tuple[Case, Situation]] = []
        self.links: list[tuple[Case, Situation, Situation, LeadsTo]] = []

    async def add_case(
        self,
        case: Case,
    ) -> None:
        self.cases.append(case)

    async def get_case(
        self,
        case_id: UUID,
    ) -> Case:
        return Case(
            case_id=case_id,
            conversation_id="1",
            created_timestamp=CREATED,
            updated_timestamp=CREATED,
        )

    async def add_situation(
        self,
        case: Case,
        situation: Situation,
    ) -> None:
        self.situations.append((case, situation))

    async def link_situations(
        self,
        case: Case,
        from_situation: Situation,
        to_situation: Situation,
        link: LeadsTo,
    ) -> None:
        self.links.append((case, from_situation, to_situation, link))

    async def lookup_leaf_situations(
        self,
        case: Case,
        start: StartSituation,
    ) -> list[Situation]:
        return []

    async def reaches_terminal(
        self,
        case: Case,
        start: StartSituation,
        terminal: TerminalSituation,
    ) -> bool:
        return False

    async def lookup_chain_so_far(
        self,
        case: Case,
        start: StartSituation,
    ) -> ChainSoFar:
        return ChainSoFar(start=start)

    async def get_chains(
        self,
    ) -> list[CausalChain]:
        return []


class _AddOnly:
    async def add_situation(
        self,
        case: Case,
        situation: Situation,
    ) -> None:
        return None


def test_causal_chain_store_requires_case_and_situation_methods():
    assert isinstance(_Both(), CausalChainStore)
    assert not isinstance(_AddOnly(), CausalChainStore)


def test_fake_records_a_situation_and_a_link():
    async def exercise():
        store = _Both()
        case = Case(
            case_id=CASE_ID,
            conversation_id="1",
            created_timestamp=CREATED,
            updated_timestamp=CREATED,
        )
        now = StartSituation(
            situation_id=NOW_ID,
            version=1,
            title="now",
            desc="now",
            potential_drivers=[],
            remained_drivers=[],
        )
        deal = Situation(situation_id=DEAL_ID, version=1, title="deal", desc="deal", remained_drivers=[])
        link = LeadsTo(
            from_situation_id=NOW_ID,
            from_version=1,
            to_situation_id=DEAL_ID,
            to_version=1,
            p=Decimal("0.08"),
        )
        await store.add_case(case)
        await store.add_situation(case, now)
        await store.link_situations(case, now, deal, link)
        return store, case, now, deal, link

    store, case, now, deal, link = asyncio.run(exercise())
    assert store.cases == [case]
    assert store.situations == [(case, now)]
    assert store.links == [(case, now, deal, link)]
