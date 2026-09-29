import asyncio
from decimal import Decimal
from uuid import UUID

from take_home.causal_chains.agents.models.messaging.causal_chain import CausalChain
from take_home.causal_chains.agents.models.causal_chains.case import Case
from take_home.causal_chains.agents.models.causal_chains.input_variable import InputVariable
from take_home.causal_chains.agents.models.causal_chains.leads_to import LeadsTo
from take_home.causal_chains.agents.models.causal_chains.situation import (
    Situation,
    StartSituation,
    TerminalSituation,
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
CASE_ID = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
OTHER_CASE_ID = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")


class _FakeGraphDb:
    def __init__(self) -> None:
        self.case_calls: list[UUID] = []
        self.situation_calls: list[tuple[UUID, int, str, UUID, str, list[str], str]] = []
        self.link_calls: list[
            tuple[UUID, int, UUID, int, Decimal, list[tuple[str, Decimal]]]
        ] = []
        self._situations: dict[
            tuple[UUID, int],
            tuple[UUID, int, str, str, list[str], str, UUID],
        ] = {}
        self._links: list[
            tuple[UUID, int, UUID, int, Decimal, list[tuple[str, Decimal]]]
        ] = []
        self._cases: set[UUID] = set()
        self.leaf_rows: list[tuple[UUID, int, str]] = []
        self.reaches = False
        self.chain_row: tuple[
            tuple[UUID, int, str, list[str]],
            list[tuple[UUID, int, str]],
            list[tuple[UUID, int, UUID, int, Decimal, list[tuple[str, Decimal]]]],
        ] | None = None

    def merge_case(self, case_id: UUID) -> None:
        self.case_calls.append(case_id)
        self._cases.add(case_id)

    def get_case(self, case_id: UUID) -> UUID | None:
        if case_id not in self._cases:
            return None
        return case_id

    def list_leaf_situations(
        self,
        case_id: UUID,
        start_situation_id: UUID,
        start_version: int,
    ) -> list[tuple[UUID, int, str]]:
        return list(self.leaf_rows)

    def reaches_terminal(
        self,
        case_id: UUID,
        start_situation_id: UUID,
        start_version: int,
        terminal_situation_id: UUID,
        terminal_version: int,
    ) -> bool:
        return self.reaches

    def lookup_chain_so_far(
        self,
        case_id: UUID,
        start_situation_id: UUID,
        start_version: int,
    ) -> tuple[
        tuple[UUID, int, str, list[str]],
        list[tuple[UUID, int, str]],
        list[tuple[UUID, int, UUID, int, Decimal, list[tuple[str, Decimal]]]],
    ] | None:
        return self.chain_row

    def merge_situation(
        self,
        situation_id: UUID,
        version: int,
        desc: str,
        case_id: UUID,
        kind: str,
        potential_factors: list[str],
        original_ask: str,
    ) -> None:
        self.situation_calls.append(
            (situation_id, version, desc, case_id, kind, potential_factors, original_ask)
        )
        self._situations[(situation_id, version)] = (
            situation_id,
            version,
            desc,
            kind,
            potential_factors,
            original_ask,
            case_id,
        )

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
    ) -> list[tuple[UUID, int, str, str, list[str], str, UUID]]:
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
        case = Case(case_id=CASE_ID)
        now = StartSituation(
            situation_id=NOW_ID,
            version=1,
            desc="now",
            potential_factors=[],
        )
        deal = Situation(situation_id=DEAL_ID, version=1, desc="deal")
        await store.add_case(case)
        await store.add_situation(case, now)
        await store.link_situations(
            case,
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
    assert graph_db.case_calls == [CASE_ID]
    assert graph_db.situation_calls == [
        (NOW_ID, 1, "now", CASE_ID, "start", [], ""),
        (NOW_ID, 1, "now", CASE_ID, "start", [], ""),
        (DEAL_ID, 1, "deal", CASE_ID, "situation", [], ""),
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
        case = Case(case_id=CASE_ID)
        await store.add_situation(case, now)
        await store.add_situation(case, other)
        await store.add_situation(case, orphan)
        await store.link_situations(case, now, deal, _link(now, deal))
        await store.link_situations(case, deal, leaf, _link(deal, leaf))
        await store.link_situations(case, other, deal, _link(other, deal))
        await store.link_situations(case, now, other, _link(now, other))
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


def test_get_chains_keeps_each_case_separate():
    async def exercise():
        graph_db = _FakeGraphDb()
        store = GraphCausalChainStore(graph_db)
        case = Case(case_id=CASE_ID)
        other_case = Case(case_id=OTHER_CASE_ID)
        now = StartSituation(
            situation_id=NOW_ID,
            version=1,
            desc="now",
            potential_factors=["blockade"],
        )
        elsewhere = StartSituation(
            situation_id=OTHER_ROOT_ID,
            version=1,
            desc="elsewhere",
            potential_factors=["talks"],
        )
        deal = Situation(situation_id=DEAL_ID, version=1, desc="deal")
        await store.add_situation(case, now)
        await store.add_situation(other_case, elsewhere)
        await store.link_situations(case, now, deal, _link(now, deal))
        return await store.get_chains()

    chains = asyncio.run(exercise())
    assert len(chains) == 2
    assert [chain.situations[0].desc for chain in chains] == ["now", "elsewhere"]
    assert chains[0].situations[0].potential_factors == ["blockade"]
    assert chains[0].links[0].to_situation_id == DEAL_ID
    assert chains[1].links == []


def test_get_case_and_leaf_lookup():
    async def exercise():
        graph_db = _FakeGraphDb()
        store = GraphCausalChainStore(graph_db)
        case = Case(case_id=CASE_ID)
        start = StartSituation(
            situation_id=NOW_ID,
            version=1,
            desc="now",
            potential_factors=["blockade"],
        )
        await store.add_case(case)
        graph_db.leaf_rows = [(LEAF_ID, 1, "leaf")]
        found = await store.get_case(CASE_ID)
        leaves = await store.lookup_leaf_situations(case, start)
        missing = None
        try:
            await store.get_case(OTHER_CASE_ID)
        except ValueError as error:
            missing = str(error)
        return found, leaves, missing

    found, leaves, missing = asyncio.run(exercise())
    assert found == Case(case_id=CASE_ID)
    assert leaves == [Situation(situation_id=LEAF_ID, version=1, desc="leaf")]
    assert missing == "case is missing"


def test_reaches_terminal_reads_the_graph():
    async def exercise():
        graph_db = _FakeGraphDb()
        store = GraphCausalChainStore(graph_db)
        case = Case(case_id=CASE_ID)
        start = StartSituation(
            situation_id=NOW_ID,
            version=1,
            desc="now",
            potential_factors=["blockade"],
        )
        terminal = TerminalSituation(
            situation_id=DEAL_ID,
            version=1,
            desc="the end",
            original_ask="the ask",
        )
        graph_db.reaches = True
        return await store.reaches_terminal(case, start, terminal)

    assert asyncio.run(exercise()) is True


def test_lookup_chain_so_far_reads_the_open_line():
    async def exercise():
        graph_db = _FakeGraphDb()
        store = GraphCausalChainStore(graph_db)
        case = Case(case_id=CASE_ID)
        start = StartSituation(
            situation_id=NOW_ID,
            version=1,
            desc="now",
            potential_factors=["blockade"],
        )
        graph_db.chain_row = (
            (NOW_ID, 1, "now", ["blockade"]),
            [],
            [],
        )
        empty = await store.lookup_chain_so_far(case, start)
        graph_db.chain_row = (
            (NOW_ID, 1, "now", ["blockade"]),
            [(DEAL_ID, 1, "talks open")],
            [
                (
                    NOW_ID,
                    1,
                    DEAL_ID,
                    1,
                    Decimal("0.5000"),
                    [("deal_odds", Decimal("0.5000"))],
                )
            ],
        )
        linked = await store.lookup_chain_so_far(case, start)
        graph_db.chain_row = None
        missing = None
        try:
            await store.lookup_chain_so_far(case, start)
        except ValueError as error:
            missing = str(error)
        return empty, linked, missing

    empty, linked, missing = asyncio.run(exercise())
    assert empty.hops == []
    assert empty.start.potential_factors == ["blockade"]
    assert linked.hops[0].situation.desc == "talks open"
    assert linked.hops[0].link.from_situation_id == NOW_ID
    assert linked.hops[0].link.to_situation_id == DEAL_ID
    assert linked.hops[0].link.p == Decimal("0.5000")
    assert missing == "start is missing"


def test_get_chains_returns_empty_when_the_graph_is_empty():
    async def exercise():
        return await GraphCausalChainStore(_FakeGraphDb()).get_chains()

    assert asyncio.run(exercise()) == []
