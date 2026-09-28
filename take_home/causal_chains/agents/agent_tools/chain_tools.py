import re
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
from take_home.causal_chains.agents.models.messaging.causal_chain import CausalChain
from take_home.causal_chains.agents.models.messaging.deeplink_card import DeeplinkCard
from take_home.causal_chains.agents.models.run_context import RunContext
from take_home.causal_chains.agents.stores.causal_chain_store.protocol.protocol import (
    CausalChainStore,
)


class LinkInput(BaseModel):
    name: str
    value: str


_WORD = re.compile(r"[a-z0-9]+")
_STOP_WORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "to",
        "of",
        "and",
        "or",
        "but",
        "during",
        "in",
        "on",
        "for",
        "is",
        "are",
        "that",
        "while",
        "with",
    }
)


def _content_words(text: str) -> list[str]:
    return [
        word
        for word in _WORD.findall(text.lower())
        if word not in _STOP_WORDS
    ]


def states_the_ask(
    desc: str,
    ask: str,
) -> bool:
    ask_words = _content_words(ask)
    desc_words = _content_words(desc)
    if not ask_words or not desc_words:
        return False
    covered = sum(1 for word in ask_words if word in set(desc_words))
    if covered / len(ask_words) < 0.8:
        return False
    return len(desc_words) <= max(len(ask_words) * 3, len(ask_words) + 12)


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
    is_end: bool,
) -> Situation:
    """Save one situation and return it, including the id assigned here.

    Args:
        ctx: Run context. The causal chain store is on its clients.
        desc: What is true in this situation.
        is_root: True only for the present.
        is_end: True only when this situation states the user's ask. Never with the root.
    """
    if is_root and is_end:
        raise ValueError("the present is not the end")
    situation = Situation(
        situation_id=uuid4(),
        version=1,
        desc=desc,
        is_root=is_root,
        is_end=is_end,
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
        from_version=from_situation.version,
        to_situation_id=to_situation.situation_id,
        to_version=to_situation.version,
        inputs=parsed,
        p=probability(parsed),
    )
    await _require_store(ctx).link_situations(
        from_situation,
        to_situation,
        link,
    )
    return link


@function_tool
async def make_deeplink_widget(
    ctx: RunContextWrapper[RunContext],
    root: Situation,
) -> DeeplinkCard:
    """Show a deeplink card for one saved root situation.

    Args:
        ctx: Run context.
        root: The stored root, including its id and version.
    """
    _require_store(ctx)
    return DeeplinkCard(
        title=root.desc,
        root_situation_id=root.situation_id,
        root_version=root.version,
    )


def _stored_situations(
    chains: list[CausalChain],
) -> list[Situation]:
    stored: dict[tuple[object, int], Situation] = {}
    for chain in chains:
        for situation in chain.situations:
            stored[(situation.situation_id, situation.version)] = situation
    return list(stored.values())


@function_tool
async def return_root(
    ctx: RunContextWrapper[RunContext],
) -> Situation | str:
    """Return the stored root after one saved situation states the user's ask.

    Args:
        ctx: Run context. The causal chain store and the user's ask are on it.
    """
    situations = _stored_situations(await _require_store(ctx).get_chains())
    ends = [situation for situation in situations if situation.is_end]
    if len(ends) != 1:
        return "Save one end situation that states the user's ask, then try again."
    end = ends[0]
    if end.is_root or not states_the_ask(end.desc, ctx.context.future_situation):
        return "The end situation must restate the user's ask, and it is not the present."
    roots = [situation for situation in situations if situation.is_root]
    if len(roots) != 1:
        return "Save one present before returning it."
    return roots[0]
