from collections import deque
from typing import override
from uuid import UUID

from take_home.causal_chains.agents.clients.graph_db.protocol.protocol import GraphDb
from take_home.causal_chains.agents.models.messaging.causal_chain import CausalChain
from take_home.causal_chains.agents.models.causal_chains.input_variable import InputVariable
from take_home.causal_chains.agents.models.causal_chains.leads_to import LeadsTo
from take_home.causal_chains.agents.models.causal_chains.situation import (
    Situation,
    StartSituation,
)
from take_home.causal_chains.agents.stores.causal_chain_store.protocol.protocol import (
    CausalChainStore,
)


def _key(
    situation_id: UUID,
    version: int,
) -> tuple[UUID, int]:
    return (situation_id, version)


def _situation_from_graph(
    situation_id: UUID,
    version: int,
    desc: str,
    is_root: bool,
) -> Situation:
    if is_root:
        return StartSituation(
            situation_id=situation_id,
            version=version,
            desc=desc,
            potential_factors=[],
        )
    return Situation(
        situation_id=situation_id,
        version=version,
        desc=desc,
    )


def chains_for(
    situations: list[Situation],
    links: list[LeadsTo],
) -> list[CausalChain]:
    unique: dict[tuple[UUID, int], Situation] = {}
    for situation in situations:
        unique.setdefault(
            _key(situation.situation_id, situation.version),
            situation,
        )
    outgoing: dict[tuple[UUID, int], list[LeadsTo]] = {}
    for link in links:
        outgoing.setdefault(
            _key(link.from_situation_id, link.from_version),
            [],
        ).append(link)
    chains: list[CausalChain] = []
    for situation in unique.values():
        if not isinstance(situation, StartSituation):
            continue
        chains.append(_chain_from(situation, unique, outgoing))
    return chains


def _chain_from(
    root: Situation,
    unique: dict[tuple[UUID, int], Situation],
    outgoing: dict[tuple[UUID, int], list[LeadsTo]],
) -> CausalChain:
    root_key = _key(root.situation_id, root.version)
    seen: dict[tuple[UUID, int], Situation] = {root_key: root}
    chain_links: list[LeadsTo] = []
    queue: deque[Situation] = deque([root])
    while queue:
        current = queue.popleft()
        current_key = _key(current.situation_id, current.version)
        for link in outgoing.get(current_key, []):
            dest_key = _key(link.to_situation_id, link.to_version)
            dest = unique.get(dest_key)
            if dest is None or isinstance(dest, StartSituation):
                continue
            chain_links.append(link)
            if dest_key not in seen:
                seen[dest_key] = dest
                queue.append(dest)
    return CausalChain(
        situations=list(seen.values()),
        links=chain_links,
    )


class GraphCausalChainStore(CausalChainStore):
    def __init__(
        self,
        graph_db: GraphDb,
    ) -> None:
        self._graph_db = graph_db

    @override
    async def add_situation(
        self,
        situation: Situation,
    ) -> None:
        self._graph_db.merge_situation(
            situation.situation_id,
            situation.version,
            situation.desc,
            isinstance(situation, StartSituation),
        )

    @override
    async def link_situations(
        self,
        from_situation: Situation,
        to_situation: Situation,
        link: LeadsTo,
    ) -> None:
        await self.add_situation(from_situation)
        await self.add_situation(to_situation)
        self._graph_db.merge_leads_to(
            link.from_situation_id,
            link.from_version,
            link.to_situation_id,
            link.to_version,
            link.p,
            [(item.name, item.value) for item in link.inputs],
        )

    @override
    async def get_chains(
        self,
    ) -> list[CausalChain]:
        situations = [
            _situation_from_graph(situation_id, version, desc, is_root)
            for situation_id, version, desc, is_root in self._graph_db.list_situations()
        ]
        links = [
            LeadsTo(
                from_situation_id=from_situation_id,
                from_version=from_version,
                to_situation_id=to_situation_id,
                to_version=to_version,
                p=p,
                inputs=[
                    InputVariable(
                        name=name,
                        value=value,
                    )
                    for name, value in inputs
                ],
            )
            for (
                from_situation_id,
                from_version,
                to_situation_id,
                to_version,
                p,
                inputs,
            ) in self._graph_db.list_leads_to()
        ]
        return chains_for(situations, links)
