from collections import defaultdict
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from take_home.causal_chains.agents.agents.crystal_ball.chain_graph import ChainGraph

_OUTGOING_SUM = "outgoing probabilities do not sum to 1"


class Exam(BaseModel):
    score: int
    failures: list[str]


def examine(graph: ChainGraph) -> Exam:
    failures: list[str] = []
    if sum(1 for situation in graph.situations if situation.is_root) != 1:
        failures.append("exactly one is_root")
    known_ids = {situation.situation_id for situation in graph.situations}
    if len(graph.destination_ids) < 2 or any(
        destination_id not in known_ids for destination_id in graph.destination_ids
    ):
        failures.append("destination_ids")
    if any(edge.p < 0 or edge.p > 1 for edge in graph.edges):
        failures.append("p is outside 0 to 1")
    if _broken_outgoing_sum(graph):
        failures.append(_OUTGOING_SUM)
    if not _two_paths_with_failure_branches(graph):
        failures.append("paths")
    return Exam(score=5 - len(failures), failures=failures)


def _broken_outgoing_sum(graph: ChainGraph) -> bool:
    totals: dict[UUID, Decimal] = defaultdict(lambda: Decimal("0"))
    for edge in graph.edges:
        totals[edge.from_situation_id] += edge.p
    return any(total != Decimal("1") for total in totals.values())


def _two_paths_with_failure_branches(graph: ChainGraph) -> bool:
    destinations = set(graph.destination_ids)
    children: dict[UUID, list[UUID]] = defaultdict(list)
    for edge in graph.edges:
        children[edge.from_situation_id].append(edge.to_situation_id)
    roots = [situation.situation_id for situation in graph.situations if situation.is_root]
    if len(roots) != 1:
        return False
    path_count = 0

    def walk(situation_id: UUID, seen: set[UUID]) -> None:
        nonlocal path_count
        if situation_id in destinations:
            path_count += 1
            return
        for child_id in children[situation_id]:
            if child_id in seen:
                continue
            walk(child_id, seen | {child_id})

    walk(roots[0], {roots[0]})
    if path_count < 2:
        return False
    for child_ids in children.values():
        reaches_destination = any(child_id in destinations for child_id in child_ids)
        has_failure = any(child_id not in destinations for child_id in child_ids)
        if reaches_destination and not has_failure:
            return False
    return True
