import asyncio
from decimal import Decimal

from agents import RunContextWrapper

from take_home.causal_chains.agents.agent_tools.chain_tools import (
    LinkInput,
    add_situation,
    link_situations,
)
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


def test_tools_write_a_situation_and_a_link_through_run_clients():
    async def exercise():
        store = _Store()
        context = RunContext(
            conversation_id="1",
            turn_id="t_1",
            clients=RunClients(causal_chain_store=store),
        )
        wrapper = RunContextWrapper(context=context)
        now = Situation.model_validate_json(
            await add_situation(wrapper, "strait shut", True)
        )
        deal = Situation.model_validate_json(
            await add_situation(wrapper, "a deal this week", False)
        )
        link = LeadsTo.model_validate_json(
            await link_situations(
                wrapper,
                str(now.situation_id),
                str(deal.situation_id),
                now.desc,
                deal.desc,
                True,
                False,
                [LinkInput(name="deal_odds", value="0.08")],
            )
        )
        return store, now, deal, link

    store, now, deal, link = asyncio.run(exercise())
    assert store.situations == [now, deal]
    assert link.p == Decimal("0.0800")
    assert store.links == [(now, deal, link)]
