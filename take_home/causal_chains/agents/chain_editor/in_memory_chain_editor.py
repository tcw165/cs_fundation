from collections import defaultdict
from decimal import Decimal
from typing import override
from uuid import UUID, uuid4

from take_home.causal_chains.agents.models.causal_chain.causal_chain import CausalChain
from take_home.causal_chains.agents.models.causal_chain.causal_link import CausalLink
from take_home.causal_chains.agents.models.causal_chain.depth_bounds import DepthBounds
from take_home.causal_chains.agents.models.causal_chain.event import Event
from take_home.causal_chains.agents.models.causal_chain.link_inputs import LinkInputs
from take_home.causal_chains.agents.models.causal_chain.price import normalize, raw_p


class InMemoryChainEditor:
    """ChainEditor that keeps one CausalChain in process memory.

    One instance is one hill-climb attempt. Depth and the child cap are
    assigned here. There is no setter for p.
    """

    def __init__(
        self,
        depth_bounds: DepthBounds | None = None,
        max_children: int = 4,
    ) -> None:
        if max_children < 2:
            raise ValueError("max_children is below 2")
        bounds = depth_bounds or DepthBounds()
        self._chain = CausalChain(depth_bounds=bounds, max_children=max_children)
        self._parent_id: dict[UUID, UUID | None] = {}

    @override
    def get_chain(self) -> CausalChain:
        return self._chain

    @override
    def get_event(self, event_id: UUID) -> Event:
        event = self._chain.events.get(event_id)
        if event is None:
            raise ValueError("event is missing")
        return event

    @override
    def list_effects(self, event_id: UUID) -> list[CausalLink]:
        self.get_event(event_id)
        return [link for link in self._chain.links.values() if link.cause_id == event_id]

    @override
    def p_query(self) -> Decimal:
        root_id = self._chain.root_id
        if root_id is None:
            return Decimal("0")
        children: dict[UUID, list[CausalLink]] = defaultdict(list)
        for link in self._chain.links.values():
            children[link.cause_id].append(link)
        total = Decimal("0")
        bounds = self._chain.depth_bounds

        def walk(event_id: UUID, product: Decimal) -> None:
            nonlocal total
            event = self._chain.events[event_id]
            if event.is_destination:
                if bounds.min_depth <= event.depth <= bounds.max_depth:
                    total += product
                return
            for link in children[event_id]:
                if link.p is None:
                    continue
                walk(link.effect_id, product * link.p)

        walk(root_id, Decimal("1"))
        return total

    @override
    def add_event(self, statement: str, cause_id: UUID | None = None) -> Event:
        if statement == "":
            raise ValueError("statement is empty")
        if cause_id is None:
            if self._chain.root_id is not None:
                raise ValueError("root already exists")
            event = Event(event_id=uuid4(), statement=statement, depth=0, is_root=True)
            self._chain.root_id = event.event_id
        else:
            cause = self._chain.events.get(cause_id)
            if cause is None:
                raise ValueError("cause is missing")
            depth = cause.depth + 1
            if depth > self._chain.depth_bounds.max_depth:
                raise ValueError("depth is past max_depth")
            event = Event(event_id=uuid4(), statement=statement, depth=depth, is_root=False)
        self._chain.events[event.event_id] = event
        self._parent_id[event.event_id] = cause_id
        return event

    @override
    def set_event(self, event_id: UUID, statement: str) -> Event:
        if statement == "":
            raise ValueError("statement is empty")
        event = self.get_event(event_id)
        event.statement = statement
        for link in self._descendant_links(event_id):
            link.stale = True
            link.p = None
        return event

    @override
    def add_link(self, cause_id: UUID, effect_id: UUID) -> CausalLink:
        cause = self._chain.events.get(cause_id)
        effect = self._chain.events.get(effect_id)
        if cause is None:
            raise ValueError("cause is missing")
        if effect is None:
            raise ValueError("effect is missing")
        if cause_id == effect_id:
            raise ValueError("self-edge")
        if effect.depth != cause.depth + 1:
            raise ValueError("skip edge")
        if self._parent_id.get(effect_id) != cause_id:
            raise ValueError("cause does not match the event parent")
        if any(link.effect_id == effect_id for link in self._chain.links.values()):
            raise ValueError("incoming link exists")
        if len(self.list_effects(cause_id)) >= self._chain.max_children:
            raise ValueError("max_children")
        link = CausalLink(link_id=uuid4(), cause_id=cause_id, effect_id=effect_id)
        self._chain.links[link.link_id] = link
        return link

    @override
    def set_link_inputs(self, link_id: UUID, inputs: LinkInputs) -> CausalLink:
        link = self._chain.links.get(link_id)
        if link is None:
            raise ValueError("link is missing")
        link.inputs = inputs
        link.raw_p = raw_p(inputs)
        link.stale = False
        self._normalize_siblings(link.cause_id)
        return link

    @override
    def mark_destination(self, event_id: UUID) -> Event:
        event = self.get_event(event_id)
        event.is_destination = True
        return event

    def _normalize_siblings(self, cause_id: UUID) -> None:
        siblings = self.list_effects(cause_id)
        if any(link.raw_p is None or link.inputs is None or link.stale for link in siblings):
            for link in siblings:
                link.p = None
            return
        raw_values: list[Decimal] = []
        for link in siblings:
            assert link.raw_p is not None
            raw_values.append(link.raw_p)
        for link, share in zip(siblings, normalize(raw_values), strict=True):
            link.p = share

    def _descendant_links(self, event_id: UUID) -> list[CausalLink]:
        children: dict[UUID, list[CausalLink]] = defaultdict(list)
        for link in self._chain.links.values():
            children[link.cause_id].append(link)
        found: list[CausalLink] = []
        stack = [event_id]
        seen = {event_id}
        while stack:
            current = stack.pop()
            for link in children[current]:
                found.append(link)
                if link.effect_id not in seen:
                    seen.add(link.effect_id)
                    stack.append(link.effect_id)
        return found
