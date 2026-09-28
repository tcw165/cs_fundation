import asyncio
import json
from decimal import Decimal
from uuid import UUID

from agents.tool_context import ToolContext

from take_home.causal_chains.agents.agent_tools.chain_tools import (
    add_situation,
    link_situations,
    make_deeplink_widget,
)
from take_home.causal_chains.agents.models.messaging.causal_chain import CausalChain
from take_home.causal_chains.agents.models.messaging.deeplink_card import DeeplinkCard
from take_home.causal_chains.agents.models.causal_chains.case import Case
from take_home.causal_chains.agents.models.causal_chains.leads_to import LeadsTo
from take_home.causal_chains.agents.models.causal_chains.situation import (
    Situation,
    StartSituation,
)
from take_home.causal_chains.agents.models.run_clients import RunClients
from take_home.causal_chains.agents.models.run_context import RunContext


class _Store:
    def __init__(self) -> None:
        self.situations: list[tuple[Case, Situation]] = []
        self.links: list[tuple[Case, Situation, Situation, LeadsTo]] = []

    async def add_case(self, case: Case) -> None:
        return None

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
        return []

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


def test_tools_write_a_situation_and_a_link_through_run_clients():
    store = _Store()
    context = RunContext(
        conversation_id="1",
        turn_id="t_1",
        clients=RunClients(causal_chain_store=store),
    )
    case = {"case_id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"}
    now = _invoke(
        add_situation,
        context,
        {"case": case, "desc": "strait shut", "is_root": True},
    )
    deal = _invoke(
        add_situation,
        context,
        {"case": case, "desc": "a deal this week", "is_root": False},
    )
    link = _invoke(
        link_situations,
        context,
        {
            "case": case,
            "from_situation": now.model_dump(
                mode="json",
                include={"situation_id", "version", "desc"},
            ),
            "to_situation": deal.model_dump(mode="json"),
            "inputs": [{"name": "deal_odds", "value": "0.08"}],
        },
    )
    assert isinstance(now, Situation)
    assert isinstance(deal, Situation)
    assert isinstance(link, LeadsTo)
    assert "Save one situation" in add_situation.description
    assert "mean of the input values" in link_situations.description
    linked_now = Situation(
        situation_id=now.situation_id,
        version=now.version,
        desc=now.desc,
    )
    stored_case = Case(case_id=UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"))
    assert store.situations == [(stored_case, now), (stored_case, deal)]
    assert link.p == Decimal("0.0800")
    assert store.links == [(stored_case, linked_now, deal, link)]
    card = _invoke(
        make_deeplink_widget,
        context,
        {"root": now.model_dump(mode="json")},
    )
    assert isinstance(card, DeeplinkCard)
    assert card.title == now.desc
    assert card.root_situation_id == now.situation_id
    assert card.root_version == now.version
    assert "deeplink card" in make_deeplink_widget.description
