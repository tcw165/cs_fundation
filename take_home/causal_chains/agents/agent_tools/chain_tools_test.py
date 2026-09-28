import asyncio
import json
from decimal import Decimal
from uuid import UUID

from agents.tool_context import ToolContext

from take_home.causal_chains.agents.agent_tools.chain_tools import (
    add_situation,
    link_situations,
    make_deeplink_widget,
    return_root,
    states_the_ask,
)
from take_home.causal_chains.agents.models.messaging.causal_chain import CausalChain
from take_home.causal_chains.agents.models.messaging.deeplink_card import DeeplinkCard
from take_home.causal_chains.agents.models.causal_chains.leads_to import LeadsTo
from take_home.causal_chains.agents.models.causal_chains.situation import Situation
from take_home.causal_chains.agents.models.run_clients import RunClients
from take_home.causal_chains.agents.models.run_context import RunContext


class _Store:
    def __init__(self) -> None:
        self.situations: list[Situation] = []
        self.links: list[tuple[Situation, Situation, LeadsTo]] = []
        self.chains: list[CausalChain] = []

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
        return self.chains


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
        {"desc": "strait shut", "is_root": True, "is_end": False},
    )
    deal = _invoke(
        add_situation,
        context,
        {"desc": "a deal this week", "is_root": False, "is_end": False},
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


ASK = "Republicans win the House but Democrats take the senate during the Midterm."
END = (
    "The future situation is that Republicans win the House while Democrats "
    "take the Senate during the midterm elections."
)


def test_states_the_ask_accepts_a_close_restatement_and_rejects_a_long_present():
    assert states_the_ask(END, ASK)
    assert not states_the_ask(" ".join([ASK] * 20), ASK)


def test_add_situation_rejects_a_root_that_is_also_the_end():
    store = _Store()
    context = RunContext(
        conversation_id="1",
        turn_id="t_1",
        clients=RunClients(causal_chain_store=store),
    )
    refused = _invoke(
        add_situation,
        context,
        {"desc": ASK, "is_root": True, "is_end": True},
    )
    assert isinstance(refused, str)
    assert "present is not the end" in refused
    assert store.situations == []


def test_return_root_waits_until_the_end_restates_the_ask():
    root = Situation(
        situation_id=UUID("11111111-1111-4111-8111-111111111111"),
        version=1,
        desc="As of today the election is still ahead.",
        is_root=True,
        is_end=False,
    )
    end = Situation(
        situation_id=UUID("22222222-2222-4222-8222-222222222222"),
        version=1,
        desc=END,
        is_root=False,
        is_end=True,
    )
    store = _Store()
    context = RunContext(
        conversation_id="1",
        turn_id="t_1",
        future_situation=ASK,
        clients=RunClients(causal_chain_store=store),
    )
    waiting = _invoke(return_root, context, {})
    assert isinstance(waiting, str)
    store.chains = [CausalChain(situations=[root, end], links=[])]
    returned = _invoke(return_root, context, {})
    assert returned == root
