import asyncio
import json
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from agents.tool_context import ToolContext


class _FixedClock:
    def now(self) -> datetime:
        return datetime(2026, 9, 29, 5, 16, tzinfo=timezone.utc)

from take_home.causal_chains.agents.agent_tools.chain_tools import (
    add_case,
    add_situation,
    add_start_situation,
    add_terminal_situation,
    get_case,
    link_situations,
    lookup_chain_so_far,
    lookup_leaf_situations,
    reaches_terminal,
)
from take_home.causal_chains.agents.models.causal_chains.chain_so_far import (
    ChainSoFar,
    LinkedHop,
)
from take_home.causal_chains.agents.models.messaging.causal_chain import CausalChain
from take_home.causal_chains.agents.models.causal_chains.case import Case
from take_home.causal_chains.agents.models.causal_chains.leads_to import LeadsTo
from take_home.causal_chains.agents.models.causal_chains.situation import (
    Situation,
)
from take_home.causal_chains.agents.models.messaging.message import MarkdownMessage
from take_home.causal_chains.agents.models.messaging.protocol.message_base import Role
from take_home.causal_chains.agents.models.run_clients import RunClients
from take_home.causal_chains.agents.models.run_context import RunContext

CREATED = datetime(2026, 10, 1, tzinfo=timezone.utc)


class _Store:
    def __init__(self) -> None:
        self.cases: list[Case] = []
        self.situations: list[tuple[Case, Situation]] = []
        self.links: list[tuple[Case, Situation, Situation, LeadsTo]] = []
        self.leaves: list[Situation] = []
        self.reaches = False
        self.line: ChainSoFar | None = None

    async def add_case(self, case: Case) -> None:
        self.cases.append(case)

    async def get_case(self, case_id: UUID) -> Case:
        for saved in self.cases:
            if saved.case_id == case_id:
                return saved
        raise ValueError("case is missing")

    async def list_latest_cases(
        self,
        conversation_id: str,
        limit: int,
    ) -> list[Case]:
        return [
            case
            for case in self.cases
            if case.conversation_id == conversation_id
        ][:limit]

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
        start: Situation,
    ) -> list[Situation]:
        return list(self.leaves)

    async def reaches_terminal(
        self,
        case: Case,
        start: Situation,
        terminal: Situation,
    ) -> bool:
        return self.reaches

    async def lookup_chain_so_far(
        self,
        case: Case,
        start: Situation,
    ) -> ChainSoFar:
        if self.line is None:
            return ChainSoFar(start=start)
        return self.line

    async def get_chains(
        self,
    ) -> list[CausalChain]:
        return []


def _invoke(
    tool: object,
    context: RunContext,
    arguments: dict[str, object],
) -> object:
    payload = json.dumps(arguments)

    async def exercise() -> object:
        return await tool.on_invoke_tool(
            ToolContext(
                context=context,
                tool_name=tool.name,
                tool_call_id="call_1",
                tool_arguments=payload,
            ),
            payload,
        )

    return asyncio.run(exercise())


def test_add_case_remembers_the_latest_user_message():
    store = _Store()
    older = MarkdownMessage(
        message_id="m_old",
        conversation_id="1",
        user_uuid="user-1",
        role=Role.user,
        text="earlier",
        created_timestamp=CREATED,
    )
    latest = older.model_copy(update={"message_id": "m_latest", "role": Role.user})
    reply = older.model_copy(update={"message_id": "m_reply", "role": Role.agent})
    context = RunContext(
        conversation_id="1",
        clock=_FixedClock(),
        turn_id="t_1",
        clients=RunClients(causal_chain_store=store),
        conversation_history=(older, latest, reply),
    )
    case = _invoke(add_case, context, {})
    assert isinstance(case, Case)
    assert case.from_message_id == "m_latest"


def test_tools_write_a_case_a_start_a_terminal_and_a_link():
    store = _Store()
    context = RunContext(
        conversation_id="1",
        clock=_FixedClock(),
        turn_id="t_1",
        clients=RunClients(causal_chain_store=store),
    )
    case = _invoke(add_case, context, {})
    assert isinstance(case, Case)
    loaded = _invoke(get_case, context, {"case_id": str(case.case_id)})
    assert loaded == case
    case_payload = case.model_dump(mode="json")
    now = _invoke(
        add_start_situation,
        context,
        {
            "case": case_payload,
            "title": "Strait shut",
            "desc": "strait shut",
            "remained_drivers": ["blockade"],
        },
    )
    deal = _invoke(
        add_situation,
        context,
        {
            "case": case_payload,
            "title": "A deal",
            "desc": "a deal this week",
            "remained_drivers": [],
        },
    )
    terminal = _invoke(
        add_terminal_situation,
        context,
        {
            "case": case_payload,
            "title": "Ships clear",
            "desc": "ships clear",
            "remained_drivers": [],
        },
    )
    link = _invoke(
        link_situations,
        context,
        {
            "case": case_payload,
            "from_situation": now.model_dump(
                mode="json",
                include={
                    "situation_id",
                    "version",
                    "kind",
                    "created_timestamp",
                    "title",
                    "desc",
                    "remained_drivers",
                },
            ),
            "to_situation": deal.model_dump(mode="json"),
            "inputs": [
                {
                    "name": "deal_odds",
                    "desc": "Odds of a deal.",
                    "probability": 0.08,
                }
            ],
        },
    )
    leaf = Situation(situation_id=UUID(int=1), version=1, created_timestamp=CREATED, kind="situation", title="leaf", desc="leaf", remained_drivers=[])
    store.leaves = [leaf]
    leaves = _invoke(
        lookup_leaf_situations,
        context,
        {"case": case_payload, "start": now.model_dump(mode="json")},
    )
    assert isinstance(now, Situation)
    assert now.kind == "start"
    assert now.remained_drivers == ["blockade"]
    assert type(deal) is Situation
    assert terminal.kind == "terminal"
    assert isinstance(link, LeadsTo)
    assert "Save the present" in add_start_situation.description
    assert "Save one mid-chain situation" in add_situation.description
    assert "mean of the input values" in link_situations.description
    assert store.cases == [case]
    assert store.situations == [(case, now), (case, deal), (case, terminal)]
    assert link.p == Decimal("0.0800")
    assert store.links == [(case, now, deal, link)]
    assert leaves == [leaf]
    store.reaches = True
    connected = _invoke(
        reaches_terminal,
        context,
        {
            "case": case_payload,
            "start": now.model_dump(mode="json"),
            "terminal": terminal.model_dump(mode="json"),
        },
    )
    assert connected is True
    assert (
        "Validate whether the start situation connects to the terminal situation."
        in reaches_terminal.description
    )
    empty_line = _invoke(
        lookup_chain_so_far,
        context,
        {"case": case_payload, "start": now.model_dump(mode="json")},
    )
    assert isinstance(empty_line, ChainSoFar)
    assert empty_line.hops == []
    mid = Situation(situation_id=deal.situation_id, version=deal.version, created_timestamp=deal.created_timestamp, kind="situation", title=deal.title, desc=deal.desc, remained_drivers=[])
    store.line = ChainSoFar(
        start=now,
        hops=[LinkedHop(situation=mid, link=link)],
    )
    linked_line = _invoke(
        lookup_chain_so_far,
        context,
        {"case": case_payload, "start": now.model_dump(mode="json")},
    )
    assert isinstance(linked_line, ChainSoFar)
    assert linked_line.hops[0].situation.desc == deal.desc
    assert linked_line.hops[0].link.to_situation_id == deal.situation_id
    assert "open line" in lookup_chain_so_far.description
    assert "saved link" in lookup_chain_so_far.description
