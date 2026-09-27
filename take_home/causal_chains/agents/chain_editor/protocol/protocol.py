from decimal import Decimal
from typing import Protocol, runtime_checkable
from uuid import UUID

from take_home.causal_chains.agents.models.causal_chain.causal_chain import CausalChain
from take_home.causal_chains.agents.models.causal_chain.causal_link import CausalLink
from take_home.causal_chains.agents.models.causal_chain.event import Event
from take_home.causal_chains.agents.models.causal_chain.link_inputs import LinkInputs


@runtime_checkable
class ChainEditor(Protocol):
    """Getters and setters for one in-memory CausalChain.

    Callers never pass p. set_link_inputs stores inputs, and the editor
    derives raw_p and the sibling share.
    """

    def get_chain(self) -> CausalChain:
        """Return the chain this editor is holding."""
        ...

    def get_event(self, event_id: UUID) -> Event:
        """Return one event. Missing ids raise ValueError."""
        ...

    def list_effects(self, event_id: UUID) -> list[CausalLink]:
        """Return the outgoing links of one event, in insertion order."""
        ...

    def p_query(self) -> Decimal:
        """Sum path products into destinations inside the depth bounds."""
        ...

    def add_event(self, statement: str, cause_id: UUID | None = None) -> Event:
        """Add an event. Omit cause_id to add the single root.

        Depth is cause.depth + 1. A hop past max_depth is rejected.
        """
        ...

    def set_event(self, event_id: UUID, statement: str) -> Event:
        """Replace the statement and mark every descendant link stale.

        Stale links lose p until set_link_inputs runs again.
        """
        ...

    def add_link(self, cause_id: UUID, effect_id: UUID) -> CausalLink:
        """Connect a cause to the effect that was created under it.

        The effect must sit exactly one hop below the cause. A cause cannot
        exceed max_children outgoing links.
        """
        ...

    def set_link_inputs(self, link_id: UUID, inputs: LinkInputs) -> CausalLink:
        """Store inputs and recompute raw_p. p is the sibling share.

        p stays unset until every sibling has inputs and none of them are stale.
        """
        ...

    def mark_destination(self, event_id: UUID) -> Event:
        """Mark an event as an outcome of the query."""
        ...
