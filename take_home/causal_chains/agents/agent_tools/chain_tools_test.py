import asyncio
import json
from decimal import Decimal

from agents.tool_context import ToolContext

from take_home.causal_chains.agents.agent_tools.chain_tools import (
    add_situation,
    link_situations,
)
from take_home.causal_chains.agents.models.messaging.causal_chain import CausalChain
from take_home.causal_chains.agents.models.causal_chains.leads_to import LeadsTo
from take_home.causal_chains.agents.models.causal_chains.situation import Situation
from take_home.causal_chains.agents.models.run_clients import RunClients
from take_home.causal_chains.agents.models.run_context import RunContext


class _Store:
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
    now = _invoke(
        add_situation,
        context,
        {"desc": "strait shut", "is_root": True},
    )
    deal = _invoke(
        add_situation,
        context,
        {"desc": "a deal this week", "is_root": False},
    )
    link = _invoke(
        link_situations,
        context,
        {
            "from_situation": now.model_dump(mode="json"),
            "to_situation": deal.model_dump(mode="json"),
            "inputs": [{"name": "deal_odds", "value": "0.08"}],
        },
    )
    assert isinstance(now, Situation)
    assert isinstance(deal, Situation)
    assert isinstance(link, LeadsTo)
    assert "Save one situation" in add_situation.description
    assert "mean of the input values" in link_situations.description
    assert store.situations == [now, deal]
    assert link.p == Decimal("0.0800")
    assert store.links == [(now, deal, link)]
