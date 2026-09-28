import asyncio
import json
from decimal import Decimal
from uuid import UUID

from agents.tool_context import ToolContext

from take_home.causal_chains.agents.agent_tools.chain_tools import (
    add_case,
    add_situation,
    add_start_situation,
    add_terminal_situation,
    get_case,
    link_situations,
    lookup_leaf_situations,
    make_deeplink_widget,
)
from take_home.causal_chains.agents.models.messaging.causal_chain import CausalChain
from take_home.causal_chains.agents.models.messaging.deeplink_card import DeeplinkCard
from take_home.causal_chains.agents.models.causal_chains.case import Case
from take_home.causal_chains.agents.models.causal_chains.leads_to import LeadsTo
from take_home.causal_chains.agents.models.causal_chains.situation import (
    Situation,
    StartSituation,
    TerminalSituation,
)
from take_home.causal_chains.agents.models.run_clients import RunClients
from take_home.causal_chains.agents.models.run_context import RunContext


class _Store:
    def __init__(self) -> None:
        self.cases: list[Case] = []
        self.situations: list[tuple[Case, Situation]] = []
        self.links: list[tuple[Case, Situation, Situation, LeadsTo]] = []
        self.leaves: list[Situation] = []

    async def add_case(self, case: Case) -> None:
        self.cases.append(case)

    async def get_case(self, case_id: UUID) -> Case:
        return Case(case_id=case_id)

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
        return list(self.leaves)

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


def test_tools_write_a_case_a_start_a_terminal_and_a_link():
    store = _Store()
    context = RunContext(
        conversation_id="1",
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
            "desc": "strait shut",
            "potential_factors": ["blockade"],
        },
    )
    deal = _invoke(
        add_situation,
        context,
        {"case": case_payload, "desc": "a deal this week"},
    )
    terminal = _invoke(
        add_terminal_situation,
        context,
        {
            "case": case_payload,
            "desc": "ships clear",
            "original_ask": "the strait opens",
        },
    )
    link = _invoke(
        link_situations,
        context,
        {
            "case": case_payload,
            "from_situation": now.model_dump(
                mode="json",
                include={"situation_id", "version", "desc"},
            ),
            "to_situation": deal.model_dump(mode="json"),
            "inputs": [{"name": "deal_odds", "value": "0.08"}],
        },
    )
    leaf = Situation(situation_id=UUID(int=1), version=1, desc="leaf")
    store.leaves = [leaf]
    leaves = _invoke(
        lookup_leaf_situations,
        context,
        {"case": case_payload, "start": now.model_dump(mode="json")},
    )
    assert isinstance(now, StartSituation)
    assert now.potential_factors == ["blockade"]
    assert type(deal) is Situation
    assert isinstance(terminal, TerminalSituation)
    assert terminal.original_ask == "the strait opens"
    assert isinstance(link, LeadsTo)
    assert "Save the present" in add_start_situation.description
    assert "Save one mid-chain situation" in add_situation.description
    assert "mean of the input values" in link_situations.description
    linked_now = Situation(
        situation_id=now.situation_id,
        version=now.version,
        desc=now.desc,
    )
    assert store.cases == [case]
    assert store.situations == [(case, now), (case, deal), (case, terminal)]
    assert link.p == Decimal("0.0800")
    assert store.links == [(case, linked_now, deal, link)]
    assert leaves == [leaf]
    card = _invoke(
        make_deeplink_widget,
        context,
        {"start": now.model_dump(mode="json")},
    )
    assert isinstance(card, DeeplinkCard)
    assert card.title == now.desc
    assert card.root_situation_id == now.situation_id
    assert card.root_version == now.version
    assert "deeplink card" in make_deeplink_widget.description
