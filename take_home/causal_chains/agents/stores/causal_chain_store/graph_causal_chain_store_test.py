import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from take_home.causal_chains.agents.models.messaging.causal_chain import CausalChain
from take_home.causal_chains.agents.models.causal_chains.case import Case
from take_home.causal_chains.agents.models.causal_chains.input_variable import InputVariable
from take_home.causal_chains.agents.models.causal_chains.leads_to import LeadsTo
from take_home.causal_chains.agents.models.causal_chains.situation import (
    Situation,
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
CREATED = datetime(2026, 10, 1, tzinfo=timezone.utc)


def _case(case_id: UUID) -> Case:
    return Case(
        case_id=case_id,
        conversation_id="1",
        from_message_id="m_1",
        created_timestamp=CREATED,
        updated_timestamp=CREATED,
    )


class _FakeGraphDb:
    def __init__(self) -> None:
        self.case_calls: list[tuple[UUID, str, str, str, str]] = []
        self.situation_calls: list[
            tuple[UUID, int, str, str, str, list[str], UUID, str]
        ] = []
        self.link_calls: list[
            tuple[UUID, int, UUID, int, Decimal, list[tuple[str, str, float]]]
        ] = []
        self._situations: dict[
            tuple[UUID, int],
            tuple[UUID, int, str, str, str, list[str], str, UUID],
        ] = {}
        self._links: list[
            tuple[UUID, int, UUID, int, Decimal, list[tuple[str, str, float]]]
        ] = []
        self._cases: dict[UUID, tuple[str, str, str, str]] = {}
        self.leaf_rows: list[tuple[UUID, int, str, str, str, list[str]]] = []
        self.reaches = False
        self.chain_row: tuple[
            tuple[UUID, int, str, str, str, list[str]],
            list[tuple[UUID, int, str, str, str, list[str]]],
            list[tuple[UUID, int, UUID, int, Decimal, list[tuple[str, str, float]]]],
        ] | None = None
        self.situation_row: tuple[
            tuple[UUID, int, str, str, str, list[str], str],
            tuple[UUID, int, str, str, str, list[str], str],
            tuple[UUID, int, str, str, str, list[str], str],
        ] | None = None

    def merge_case(
        self,
        case_id: UUID,
        conversation_id: str,
        from_message_id: str,
        created_timestamp: str,
        updated_timestamp: str,
    ) -> None:
        self.case_calls.append(
            (
                case_id,
                conversation_id,
                from_message_id,
                created_timestamp,
                updated_timestamp,
            )
        )
        self._cases[case_id] = (
            conversation_id,
            from_message_id,
            created_timestamp,
            updated_timestamp,
        )

    def get_case(self, case_id: UUID) -> tuple[UUID, str, str, str, str] | None:
        stored = self._cases.get(case_id)
        if stored is None:
            return None
        conversation_id, from_message_id, created_timestamp, updated_timestamp = stored
        return (
            case_id,
            conversation_id,
            from_message_id,
            created_timestamp,
            updated_timestamp,
        )

    def list_latest_cases(
        self,
        conversation_id: str,
        limit: int,
    ) -> list[tuple[UUID, str, str, str, str]]:
        rows = [
            (case_id, *stored)
            for case_id, stored in self._cases.items()
            if stored[0] == conversation_id
        ]
        rows.sort(key=lambda row: row[3], reverse=True)
        return rows[:limit]

    def list_leaf_situations(
        self,
        case_id: UUID,
        start_situation_id: UUID,
        start_version: int,
    ) -> list[tuple[UUID, int, str, str, str, list[str]]]:
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

    def lookup_situation(
        self,
        situation_id: UUID,
    ) -> tuple[
        tuple[UUID, int, str, str, str, list[str], str],
        tuple[UUID, int, str, str, str, list[str], str],
        tuple[UUID, int, str, str, str, list[str], str],
    ] | None:
        return self.situation_row

    def lookup_chain_so_far(
        self,
        case_id: UUID,
        start_situation_id: UUID,
        start_version: int,
    ) -> tuple[
        tuple[UUID, int, str, str, str, list[str], list[str]],
        list[tuple[UUID, int, str, str, str, list[str]]],
        list[tuple[UUID, int, UUID, int, Decimal, list[tuple[str, str, float]]]],
    ] | None:
        return self.chain_row

    def merge_situation(
        self,
        situation_id: UUID,
        version: int,
        created_timestamp: str,
        title: str,
        desc: str,
        remained_drivers: list[str],
        case_id: UUID,
        kind: str,
    ) -> None:
        self.situation_calls.append(
            (
                situation_id,
                version,
                created_timestamp,
                title,
                desc,
                remained_drivers,
                case_id,
                kind,
            )
        )
        self._situations[(situation_id, version)] = (
            situation_id,
            version,
            created_timestamp,
            title,
            desc,
            remained_drivers,
            kind,
            case_id,
        )

    def merge_leads_to(
        self,
        from_situation_id: UUID,
        from_version: int,
        to_situation_id: UUID,
        to_version: int,
        p: Decimal,
        inputs: list[tuple[str, str, float]],
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
    ) -> list[tuple[UUID, int, str, str, str, list[str], str, UUID]]:
        return list(self._situations.values())

    def list_leads_to(
        self,
    ) -> list[tuple[UUID, int, UUID, int, Decimal, list[tuple[str, str, float]]]]:
        return list(self._links)


def test_graph_causal_chain_store_is_a_causal_chain_store():
    assert isinstance(GraphCausalChainStore(_FakeGraphDb()), CausalChainStore)


def test_add_situation_and_link_situations_record_calls():
    async def exercise():
        graph_db = _FakeGraphDb()
        store = GraphCausalChainStore(graph_db)
        case = _case(CASE_ID)
        now = Situation(
            situation_id=NOW_ID,
            version=1,
            created_timestamp=CREATED,
            kind="start",
            title="now",
            desc="now",
            remained_drivers=[],
        )
        deal = Situation(situation_id=DEAL_ID, version=1, created_timestamp=CREATED, kind="situation", title="deal", desc="deal", remained_drivers=[])
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
                inputs=[
                    InputVariable(
                        name="deal_odds",
                        desc="Odds of a deal.",
                        probability=0.08,
                    )
                ],
                p=Decimal("0.0800"),
            ),
        )
        return graph_db

    graph_db = asyncio.run(exercise())
    assert graph_db.case_calls == [
        (CASE_ID, "1", "m_1", CREATED.isoformat(), CREATED.isoformat())
    ]
    assert graph_db.situation_calls == [
        (NOW_ID, 1, CREATED.isoformat(), "now", "now", [], CASE_ID, "start"),
        (NOW_ID, 1, CREATED.isoformat(), "now", "now", [], CASE_ID, "start"),
        (DEAL_ID, 1, CREATED.isoformat(), "deal", "deal", [], CASE_ID, "situation"),
    ]
    assert graph_db.link_calls == [
        (
            NOW_ID,
            1,
            DEAL_ID,
            1,
            Decimal("0.0800"),
            [("deal_odds", "Odds of a deal.", 0.08)],
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
        now = Situation(
            situation_id=NOW_ID,
            version=1,
            created_timestamp=CREATED,
            kind="start",
            title="now",
            desc="now",
            remained_drivers=[],
        )
        other = Situation(
            situation_id=OTHER_ROOT_ID,
            version=1,
            created_timestamp=CREATED,
            kind="start",
            title="other",
            desc="other",
            remained_drivers=[],
        )
        deal = Situation(situation_id=DEAL_ID, version=1, created_timestamp=CREATED, kind="situation", title="deal", desc="deal", remained_drivers=[])
        leaf = Situation(situation_id=LEAF_ID, version=1, created_timestamp=CREATED, kind="situation", title="leaf", desc="leaf", remained_drivers=[])
        orphan = Situation(
            situation_id=UUID("55555555-5555-4555-8555-555555555555"),
            version=1,
            created_timestamp=CREATED,
            kind="situation",
            title="orphan",
            desc="orphan",
            remained_drivers=[],
        )
        case = _case(CASE_ID)
        await store.add_situation(case, now)
        await store.add_situation(case, other)
        await store.add_situation(case, orphan)
        await store.link_situations(case, now, deal, _link(now, deal))
        await store.link_situations(case, deal, leaf, _link(deal, leaf))
        await store.link_situations(case, other, deal, _link(other, deal))
        await store.link_situations(case, now, other, _link(now, other))
        return await store.get_chains()

    chains = asyncio.run(exercise())
    now = Situation(
        situation_id=NOW_ID,
        version=1,
        created_timestamp=CREATED,
        kind="start",
        title="now",
        desc="now",
        remained_drivers=[],
    )
    other = Situation(
        situation_id=OTHER_ROOT_ID,
        version=1,
        created_timestamp=CREATED,
        kind="start",
        title="other",
        desc="other",
        remained_drivers=[],
    )
    deal = Situation(situation_id=DEAL_ID, version=1, created_timestamp=CREATED, kind="situation", title="deal", desc="deal", remained_drivers=[])
    leaf = Situation(situation_id=LEAF_ID, version=1, created_timestamp=CREATED, kind="situation", title="leaf", desc="leaf", remained_drivers=[])
    assert chains == [
        CausalChain(
            situations=[now, deal, leaf],
            links=[_link(now, deal), _link(deal, leaf)],
            case_id=CASE_ID,
        ),
        CausalChain(
            situations=[other, deal, leaf],
            links=[_link(other, deal), _link(deal, leaf)],
            case_id=CASE_ID,
        ),
    ]


def test_get_chains_keeps_each_case_separate():
    async def exercise():
        graph_db = _FakeGraphDb()
        store = GraphCausalChainStore(graph_db)
        case = _case(CASE_ID)
        other_case = _case(OTHER_CASE_ID)
        now = Situation(
            situation_id=NOW_ID,
            version=1,
            created_timestamp=CREATED,
            kind="start",
            title="now",
            desc="now",
            remained_drivers=[],
        )
        elsewhere = Situation(
            situation_id=OTHER_ROOT_ID,
            version=1,
            created_timestamp=CREATED,
            kind="start",
            title="elsewhere",
            desc="elsewhere",
            remained_drivers=[],
        )
        deal = Situation(situation_id=DEAL_ID, version=1, created_timestamp=CREATED, kind="situation", title="deal", desc="deal", remained_drivers=[])
        await store.add_situation(case, now)
        await store.add_situation(other_case, elsewhere)
        await store.link_situations(case, now, deal, _link(now, deal))
        return await store.get_chains()

    chains = asyncio.run(exercise())
    assert len(chains) == 2
    assert [chain.case_id for chain in chains] == [CASE_ID, OTHER_CASE_ID]
    assert [chain.situations[0].desc for chain in chains] == ["now", "elsewhere"]
    assert chains[0].situations[0].kind == "start"
    assert chains[0].links[0].to_situation_id == DEAL_ID
    assert chains[1].links == []


def test_get_chains_follows_a_link_onto_another_case():
    async def exercise():
        graph_db = _FakeGraphDb()
        store = GraphCausalChainStore(graph_db)
        created = CREATED.isoformat()
        graph_db.merge_situation(NOW_ID, 1, created, "now", "now", [], CASE_ID, "start")
        graph_db.merge_situation(DEAL_ID, 1, created, "deal", "deal", [], CASE_ID, "situation")
        graph_db.merge_situation(
            LEAF_ID,
            1,
            created,
            "fork",
            "fork",
            [],
            OTHER_CASE_ID,
            "situation",
        )
        graph_db.merge_leads_to(NOW_ID, 1, DEAL_ID, 1, Decimal("1"), [])
        graph_db.merge_leads_to(DEAL_ID, 1, LEAF_ID, 1, Decimal("1"), [])
        return await store.get_chains()

    chains = asyncio.run(exercise())
    assert len(chains) == 1
    assert chains[0].case_id == CASE_ID
    assert {situation.situation_id for situation in chains[0].situations} == {
        NOW_ID,
        DEAL_ID,
        LEAF_ID,
    }
    assert len(chains[0].links) == 2


def test_get_case_and_leaf_lookup():
    async def exercise():
        graph_db = _FakeGraphDb()
        store = GraphCausalChainStore(graph_db)
        case = _case(CASE_ID)
        start = Situation(
            situation_id=NOW_ID,
            version=1,
            created_timestamp=CREATED,
            kind="start",
            title="now",
            desc="now",
            remained_drivers=[],
        )
        await store.add_case(case)
        graph_db.leaf_rows = [(LEAF_ID, 1, CREATED.isoformat(), "leaf", "leaf", [])]
        found = await store.get_case(CASE_ID)
        leaves = await store.lookup_leaf_situations(case, start)
        missing = None
        try:
            await store.get_case(OTHER_CASE_ID)
        except ValueError as error:
            missing = str(error)
        return found, leaves, missing

    found, leaves, missing = asyncio.run(exercise())
    assert found == _case(CASE_ID)
    assert leaves == [Situation(situation_id=LEAF_ID, version=1, created_timestamp=CREATED, kind="situation", title="leaf", desc="leaf", remained_drivers=[])]
    assert missing == "case is missing"


def test_reaches_terminal_reads_the_graph():
    async def exercise():
        graph_db = _FakeGraphDb()
        store = GraphCausalChainStore(graph_db)
        case = _case(CASE_ID)
        start = Situation(
            situation_id=NOW_ID,
            version=1,
            created_timestamp=CREATED,
            kind="start",
            title="now",
            desc="now",
            remained_drivers=[],
        )
        terminal = Situation(
            situation_id=DEAL_ID,
            version=1,
            created_timestamp=CREATED,
            kind="terminal",
            title="the end",
            desc="the end",
            remained_drivers=[],
        )
        graph_db.reaches = True
        return await store.reaches_terminal(case, start, terminal)

    assert asyncio.run(exercise()) is True


def test_lookup_situation_reads_the_parent_and_terminal():
    async def exercise():
        graph_db = _FakeGraphDb()
        store = GraphCausalChainStore(graph_db)
        graph_db.situation_row = (
            (DEAL_ID, 1, CREATED.isoformat(), "talks", "talks", ["deal"], "situation"),
            (NOW_ID, 1, CREATED.isoformat(), "now", "now", ["deal"], "start"),
            (LEAF_ID, 1, CREATED.isoformat(), "end", "the end", [], "terminal"),
        )
        found = await store.lookup_situation(DEAL_ID)
        graph_db.situation_row = None
        missing = None
        try:
            await store.lookup_situation(DEAL_ID)
        except ValueError as error:
            missing = str(error)
        return found, missing

    found, missing = asyncio.run(exercise())
    current, parent, terminal = found
    assert current.situation_id == DEAL_ID
    assert current.kind == "situation"
    assert parent.situation_id == NOW_ID
    assert parent.kind == "start"
    assert terminal.situation_id == LEAF_ID
    assert terminal.kind == "terminal"
    assert missing == "situation is missing"


def test_lookup_chain_so_far_reads_the_open_line():
    async def exercise():
        graph_db = _FakeGraphDb()
        store = GraphCausalChainStore(graph_db)
        case = _case(CASE_ID)
        start = Situation(
            situation_id=NOW_ID,
            version=1,
            created_timestamp=CREATED,
            kind="start",
            title="now",
            desc="now",
            remained_drivers=[],
        )
        graph_db.chain_row = (
            (NOW_ID, 1, CREATED.isoformat(), "now", "now", []),
            [],
            [],
        )
        empty = await store.lookup_chain_so_far(case, start)
        graph_db.chain_row = (
            (NOW_ID, 1, CREATED.isoformat(), "now", "now", []),
            [(DEAL_ID, 1, CREATED.isoformat(), "talks", "talks open", [])],
            [
                (
                    NOW_ID,
                    1,
                    DEAL_ID,
                    1,
                    Decimal("0.5000"),
                    [("deal_odds", "Odds of a deal.", 0.5)],
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
    assert empty.start.kind == "start"
    assert linked.hops[0].situation.desc == "talks open"
    assert linked.hops[0].link.from_situation_id == NOW_ID
    assert linked.hops[0].link.to_situation_id == DEAL_ID
    assert linked.hops[0].link.p == Decimal("0.5000")
    assert missing == "start is missing"


def test_get_chains_returns_empty_when_the_graph_is_empty():
    async def exercise():
        return await GraphCausalChainStore(_FakeGraphDb()).get_chains()

    assert asyncio.run(exercise()) == []


def test_list_latest_cases_returns_the_newest_for_the_conversation():
    async def exercise():
        store = GraphCausalChainStore(_FakeGraphDb())
        older = _case(CASE_ID)
        newer = _case(OTHER_CASE_ID).model_copy(
            update={
                "created_timestamp": datetime(2026, 10, 2, tzinfo=timezone.utc),
                "from_message_id": "m_new",
            }
        )
        elsewhere = newer.model_copy(
            update={"case_id": OTHER_ROOT_ID, "conversation_id": "2"}
        )
        await store.add_case(older)
        await store.add_case(newer)
        await store.add_case(elsewhere)
        return await store.list_latest_cases("1", limit=1)

    listed = asyncio.run(exercise())
    assert [case.case_id for case in listed] == [OTHER_CASE_ID]
    assert listed[0].from_message_id == "m_new"
