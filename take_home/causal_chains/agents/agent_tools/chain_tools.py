from decimal import Decimal
from uuid import UUID, uuid4

from agents import RunContextWrapper, function_tool
from pydantic import BaseModel

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
async def add_case(
    ctx: RunContextWrapper[RunContext],
) -> Case:
    """Create a case and return it, including the id assigned here.

    Args:
        ctx: Run context. The causal chain store is on its clients.
    """
    case = Case(case_id=uuid4(), conversation_id=ctx.context.conversation_id)
    await _require_store(ctx).add_case(case)
    return case


@function_tool
async def get_case(
    ctx: RunContextWrapper[RunContext],
    case_id: UUID,
) -> Case:
    """Load one case by the id assigned when it was created.

    Args:
        ctx: Run context. The causal chain store is on its clients.
        case_id: The id of the case to load.
    """
    return await _require_store(ctx).get_case(case_id)


@function_tool
async def add_start_situation(
    ctx: RunContextWrapper[RunContext],
    case: Case,
    desc: str,
    potential_factors: list[str],
) -> StartSituation:
    """Save the present on a case and return it, including the id assigned here.

    Args:
        ctx: Run context. The causal chain store is on its clients.
        case: The case this start belongs to.
        desc: What is true in the present, including the context behind it.
        potential_factors: The drivers behind this present.
    """
    situation = StartSituation(
        situation_id=uuid4(),
        version=1,
        desc=desc,
        potential_factors=potential_factors,
    )
    await _require_store(ctx).add_situation(case, situation)
    return situation


@function_tool
async def add_situation(
    ctx: RunContextWrapper[RunContext],
    case: Case,
    desc: str,
) -> Situation:
    """Save one mid-chain situation on a case and return it, including the id assigned here.

    Args:
        ctx: Run context. The causal chain store is on its clients.
        case: The case this situation belongs to.
        desc: What is true in this situation.
    """
    situation = Situation(
        situation_id=uuid4(),
        version=1,
        desc=desc,
    )
    await _require_store(ctx).add_situation(case, situation)
    return situation


@function_tool
async def add_terminal_situation(
    ctx: RunContextWrapper[RunContext],
    case: Case,
    desc: str,
    original_ask: str,
) -> TerminalSituation:
    """Save the future on a case and return it, including the id assigned here.

    Args:
        ctx: Run context. The causal chain store is on its clients.
        case: The case this terminal belongs to.
        desc: What is true in the future, in your own words, including the current time.
        original_ask: The user's ask, kept with the terminal.
    """
    situation = TerminalSituation(
        situation_id=uuid4(),
        version=1,
        desc=desc,
        original_ask=original_ask,
    )
    await _require_store(ctx).add_situation(case, situation)
    return situation


@function_tool
async def link_situations(
    ctx: RunContextWrapper[RunContext],
    case: Case,
    from_situation: Situation,
    to_situation: Situation,
    inputs: list[LinkInput],
) -> LeadsTo:
    """Save both situations and the leads-to link between them.

    The stored probability is the mean of the input values. Do not pass a probability.

    Args:
        ctx: Run context. The causal chain store is on its clients.
        case: The case both situations belong to.
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
    case: Case,
    start: StartSituation,
) -> list[Situation]:
    """Return mid-chain situations reached from the start that have no outgoing link.

    The start and any terminal are left out. An empty list means the frontier is still the start.

    Args:
        ctx: Run context. The causal chain store is on its clients.
        case: The case to search.
        start: The saved start to walk from.
    """
    return await _require_store(ctx).lookup_leaf_situations(case, start)


@function_tool
async def reaches_terminal(
    ctx: RunContextWrapper[RunContext],
    case: Case,
    start: StartSituation,
    terminal: TerminalSituation,
) -> bool:
    """Validate whether the start situation connects to the terminal situation.

    Args:
        ctx: Run context. The causal chain store is on its clients.
        case: The case both situations belong to.
        start: The saved start.
        terminal: The saved terminal.
    """
    return await _require_store(ctx).reaches_terminal(case, start, terminal)


@function_tool
async def lookup_chain_so_far(
    ctx: RunContextWrapper[RunContext],
    case: Case,
    start: StartSituation,
) -> ChainSoFar:
    """Load the open line from the present through the current situation, including each saved link.

    The terminal is not included. An empty hop list means nothing is linked yet.

    Args:
        ctx: Run context. The causal chain store is on its clients.
        case: The case to read.
        start: The saved start to walk from.
    """
    return await _require_store(ctx).lookup_chain_so_far(case, start)
