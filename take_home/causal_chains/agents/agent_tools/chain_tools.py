from decimal import Decimal
from uuid import UUID, uuid4

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


def _store(
    ctx: RunContextWrapper[RunContext],
) -> CausalChainStore:
    store = ctx.context.clients.causal_chain_store
    if not isinstance(store, CausalChainStore):
        raise ValueError("causal chain store is missing")
    return store


async def add_situation(
    ctx: RunContextWrapper[RunContext],
    desc: str,
    is_root: bool,
) -> str:
    situation = Situation(
        situation_id=uuid4(),
        desc=desc,
        is_root=is_root,
    )
    await _store(ctx).add_situation(situation)
    return situation.model_dump_json()


async def link_situations(
    ctx: RunContextWrapper[RunContext],
    from_situation_id: str,
    to_situation_id: str,
    from_desc: str,
    to_desc: str,
    from_is_root: bool,
    to_is_root: bool,
    inputs: list[LinkInput],
) -> str:
    parsed = [
        InputVariable(
            name=item.name,
            value=Decimal(item.value),
        )
        for item in inputs
    ]
    from_situation = Situation(
        situation_id=UUID(from_situation_id),
        desc=from_desc,
        is_root=from_is_root,
    )
    to_situation = Situation(
        situation_id=UUID(to_situation_id),
        desc=to_desc,
        is_root=to_is_root,
    )
    link = LeadsTo(
        from_situation_id=from_situation.situation_id,
        to_situation_id=to_situation.situation_id,
        inputs=parsed,
        p=probability(parsed),
    )
    await _store(ctx).link_situations(
        from_situation,
        to_situation,
        link,
    )
    return link.model_dump_json()


add_situation_tool = function_tool(
    add_situation,
    description_override="Write one situation and return it.",
)
link_situations_tool = function_tool(
    link_situations,
    description_override=(
        "Write a leads-to link. The probability is the mean of the input values."
    ),
)
