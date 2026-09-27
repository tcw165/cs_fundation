from collections import defaultdict
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from take_home.causal_chains.agents.models.causal_chain.causal_chain import CausalChain

_OUTGOING_SUM = "outgoing probabilities do not sum to 1"


class Exam(BaseModel):
    """Score for one CausalChain. failures are the checks that did not pass."""

    score: int
    failures: list[str]


def examine(chain: CausalChain) -> Exam:
    """Score a chain from 0 to 5. Each failed check costs one point.

    A cause may have more than two effects. Every non-leaf still needs at
    least two, and those probabilities must sum to 1. A failure arm is not
    required when every child is a destination.
    """
    failures: list[str] = []
    roots = [event for event in chain.events.values() if event.is_root]
    if len(roots) != 1 or chain.root_id is None:
        failures.append("exactly one is_root")
    bounds = chain.depth_bounds
    destinations = [event for event in chain.events.values() if event.is_destination]
    if len(destinations) < 2 or any(
        event.depth < bounds.min_depth or event.depth > bounds.max_depth for event in destinations
    ):
        failures.append("destinations")
    if any(link.p is None for link in chain.links.values()):
        failures.append("p is unset")
    elif any(link.p is not None and (link.p < 0 or link.p > 1) for link in chain.links.values()):
        failures.append("p is outside 0 to 1")
    if not any(link.p is None for link in chain.links.values()) and _broken_outgoing_sum(chain):
        failures.append(_OUTGOING_SUM)
    if not _two_paths(chain):
        failures.append("paths")
    if _bad_children(chain):
        failures.append("children")
    return Exam(score=5 - len(failures), failures=failures)


def _broken_outgoing_sum(chain: CausalChain) -> bool:
    totals: dict[UUID, Decimal] = defaultdict(lambda: Decimal("0"))
    for link in chain.links.values():
        if link.p is None:
            return True
        totals[link.cause_id] += link.p
    return any(total != Decimal("1") for total in totals.values())


def _two_paths(chain: CausalChain) -> bool:
    if chain.root_id is None:
        return False
    destinations = {event.event_id for event in chain.events.values() if event.is_destination}
    children: dict[UUID, list[UUID]] = defaultdict(list)
    for link in chain.links.values():
        children[link.cause_id].append(link.effect_id)
    path_count = 0

    def walk(event_id: UUID, seen: set[UUID]) -> None:
        nonlocal path_count
        if event_id in destinations:
            path_count += 1
            return
        for child_id in children[event_id]:
            if child_id in seen:
                continue
            walk(child_id, seen | {child_id})

    walk(chain.root_id, {chain.root_id})
    return path_count >= 2


def _bad_children(chain: CausalChain) -> bool:
    counts: dict[UUID, int] = defaultdict(int)
    for link in chain.links.values():
        counts[link.cause_id] += 1
    return any(count < 2 or count > chain.max_children for count in counts.values())
