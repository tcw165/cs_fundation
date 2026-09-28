from decimal import Decimal
from uuid import uuid4

from agents import RunContextWrapper, function_tool
from pydantic import BaseModel

from take_home.causal_chains.agents.models.causal_chains.input_variable import (
    InputVariable,
    probability,
)
from take_home.causal_chains.agents.models.causal_chains.leads_to import LeadsTo
from take_home.causal_chains.agents.models.causal_chains.situation import Situation
from take_home.causal_chains.agents.models.run_context import RunContext
from take_home.causal_chains.agents.stores.causal_chain_store.protocol.protocol import (
    CausalChainStore,
)


class LinkInput(BaseModel):
    name: str
    value: str


def _require_store(
    ctx: RunContextWrapper[RunContext],
) -> CausalChainStore:
    store = ctx.context.clients.causal_chain_store
    if not isinstance(store, CausalChainStore):
        raise ValueError("causal chain store is missing")
    return store


@function_tool
async def add_situation(
    ctx: RunContextWrapper[RunContext],
    desc: str,
    is_root: bool,
) -> Situation:
    """Save one situation and return it, including the id assigned here.

    Args:
        ctx: Run context. The causal chain store is on its clients.
        desc: What is true in this situation.
        is_root: True only for the present.
    """
    situation = Situation(
        situation_id=uuid4(),
        desc=desc,
        is_root=is_root,
    )
    await _require_store(ctx).add_situation(situation)
    return situation


@function_tool
async def link_situations(
    ctx: RunContextWrapper[RunContext],
    from_situation: Situation,
    to_situation: Situation,
    inputs: list[LinkInput],
) -> LeadsTo:
    """Save both situations and the leads-to link between them.

    The stored probability is the mean of the input values. Do not pass a probability.

    Args:
        ctx: Run context. The causal chain store is on its clients.
        from_situation: The situation this link leaves.
        to_situation: The situation this link reaches.
        inputs: Named values between 0 and 1 that a person could move later.
    """
    parsed = [
        InputVariable(
            name=item.name,
            value=Decimal(item.value),
        )
        for item in inputs
    ]
    link = LeadsTo(
        from_situation_id=from_situation.situation_id,
        to_situation_id=to_situation.situation_id,
        inputs=parsed,
        p=probability(parsed),
    )
    await _require_store(ctx).link_situations(
        from_situation,
        to_situation,
        link,
    )
    return link
