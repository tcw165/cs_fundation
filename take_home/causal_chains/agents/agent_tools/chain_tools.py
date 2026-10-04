from typing import Annotated
from uuid import UUID, uuid4

from agents import RunContextWrapper, function_tool
from pydantic import BaseModel, Field

from take_home.causal_chains.agents.models.causal_chains.case import Case
from take_home.causal_chains.agents.models.causal_chains.chain_so_far import ChainSoFar
from take_home.causal_chains.agents.models.causal_chains.input_variable import (
    InputVariable,
    probability,
)
from take_home.causal_chains.agents.models.causal_chains.leads_to import LeadsTo
from take_home.causal_chains.agents.models.causal_chains.situation import (
    Situation,
    StartSituation,
    TerminalSituation,
)
from take_home.causal_chains.agents.models.run_context import RunContext
from take_home.causal_chains.agents.stores.causal_chain_store.protocol.protocol import (
    CausalChainStore,
)


class LinkInput(BaseModel):
    name: str = Field(..., description="A short name for this input.")
    desc: str = Field(
        ...,
        description="What this input is, and why this driver could change the situation.",
    )
    probability: float = Field(
        ...,
        ge=0,
        le=1,
        description="A number between 0 and 1 for a driver that could change the situation.",
    )


def _require_store(
    ctx: RunContextWrapper[RunContext],
) -> CausalChainStore:
    store = ctx.context.clients.causal_chain_store
    if not isinstance(store, CausalChainStore):
        raise ValueError("causal chain store is missing")
    return store


@function_tool
async def add_case(
    ctx: RunContextWrapper[RunContext],
) -> Case:
    """Create a case and return it, including the id assigned here."""
    created = ctx.context.clock.now()
    case = Case(
        case_id=uuid4(),
        conversation_id=ctx.context.conversation_id,
        created_timestamp=created,
        updated_timestamp=created,
    )
    await _require_store(ctx).add_case(case)
    return case


@function_tool
async def get_case(
    ctx: RunContextWrapper[RunContext],
    case_id: Annotated[UUID, "The id of the case to load."],
) -> Case:
    """Load one case by the id assigned when it was created."""
    return await _require_store(ctx).get_case(case_id)


@function_tool
async def add_start_situation(
    ctx: RunContextWrapper[RunContext],
    case: Annotated[Case, "The case this start belongs to."],
    title: Annotated[str, "A short and readable description within 100 words."],
    desc: Annotated[
        str,
        "What is true in the present, including the context behind it.",
    ],
    potential_drivers: Annotated[list[str], "The drivers behind this present."],
    remained_drivers: Annotated[
        list[str],
        "Drivers from the start situation still left to change.",
    ],
) -> StartSituation:
    """Save the present on a case and return it, including the id assigned here."""
    situation = StartSituation(
        situation_id=uuid4(),
        version=1,
        title=title,
        desc=desc,
        remained_drivers=remained_drivers,
        potential_drivers=potential_drivers,
    )
    await _require_store(ctx).add_situation(case, situation)
    return situation


@function_tool
async def add_situation(
    ctx: RunContextWrapper[RunContext],
    case: Annotated[Case, "The case this situation belongs to."],
    title: Annotated[str, "A short and readable description within 100 words."],
    desc: Annotated[str, "Detailed statements in this situation (much longer than title)."],
    remained_drivers: Annotated[
        list[str],
        "Drivers from the start situation still left to change.",
    ],
) -> Situation:
    """Save one mid-chain situation on a case and return it, including the id assigned here."""
    situation = Situation(
        situation_id=uuid4(),
        version=1,
        title=title,
        desc=desc,
        remained_drivers=remained_drivers,
    )
    await _require_store(ctx).add_situation(case, situation)
    return situation


@function_tool
async def add_terminal_situation(
    ctx: RunContextWrapper[RunContext],
    case: Annotated[Case, "The case this terminal belongs to."],
    title: Annotated[str, "A short and readable description within 100 words."],
    desc: Annotated[
        str,
        "What is true in the future, in your own words, including the current time.",
    ],
    original_ask: Annotated[str, "The user's ask, kept with the terminal."],
    remained_drivers: Annotated[
        list[str],
        "Drivers from the start situation still left to change.",
    ],
) -> TerminalSituation:
    """Save the future on a case and return it, including the id assigned here."""
    situation = TerminalSituation(
        situation_id=uuid4(),
        version=1,
        title=title,
        desc=desc,
        remained_drivers=remained_drivers,
        original_ask=original_ask,
    )
    await _require_store(ctx).add_situation(case, situation)
    return situation


@function_tool
async def link_situations(
    ctx: RunContextWrapper[RunContext],
    case: Annotated[Case, "The case both situations belong to."],
    from_situation: Annotated[Situation, "The situation this link leaves."],
    to_situation: Annotated[Situation, "The situation this link reaches."],
    inputs: Annotated[
        list[LinkInput],
        "Named values between 0 and 1 for a driver that could change the situation.",
    ],
) -> LeadsTo:
    """Save both situations and the leads-to link between them.

    The stored probability is the mean of the input values. Do not pass a probability.
    """
    parsed = [
        InputVariable(
            name=item.name,
            desc=item.desc,
            probability=item.probability,
        )
        for item in inputs
    ]
    link = LeadsTo(
        from_situation_id=from_situation.situation_id,
        from_version=from_situation.version,
        to_situation_id=to_situation.situation_id,
        to_version=to_situation.version,
        inputs=parsed,
        p=probability(parsed),
    )
    await _require_store(ctx).link_situations(
        case,
        from_situation,
        to_situation,
        link,
    )
    return link


@function_tool
async def lookup_leaf_situations(
    ctx: RunContextWrapper[RunContext],
    case: Annotated[Case, "The case to search."],
    start: Annotated[StartSituation, "The saved start to walk from."],
) -> list[Situation]:
    """Return mid-chain situations reached from the start that have no outgoing link.

    The start and any terminal are left out. An empty list means the frontier is still the start.
    """
    return await _require_store(ctx).lookup_leaf_situations(case, start)


@function_tool
async def reaches_terminal(
    ctx: RunContextWrapper[RunContext],
    case: Annotated[Case, "The case both situations belong to."],
    start: Annotated[StartSituation, "The saved start."],
    terminal: Annotated[TerminalSituation, "The saved terminal."],
) -> bool:
    """Validate whether the start situation connects to the terminal situation."""
    return await _require_store(ctx).reaches_terminal(case, start, terminal)


@function_tool
async def lookup_chain_so_far(
    ctx: RunContextWrapper[RunContext],
    case: Annotated[Case, "The case to read."],
    start: Annotated[StartSituation, "The saved start to walk from."],
) -> ChainSoFar:
    """Load the open line from the present through the current situation, including each saved link.

    The terminal is not included. An empty hop list means nothing is linked yet.
    """
    return await _require_store(ctx).lookup_chain_so_far(case, start)
