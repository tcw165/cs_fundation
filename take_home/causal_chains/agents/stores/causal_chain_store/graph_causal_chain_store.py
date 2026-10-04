from collections import deque
from datetime import datetime
from typing import Literal, override
from uuid import UUID

from take_home.causal_chains.agents.clients.graph_db.protocol.protocol import GraphDb
from take_home.causal_chains.agents.models.messaging.causal_chain import CausalChain
from take_home.causal_chains.agents.models.causal_chains.case import Case
from take_home.causal_chains.agents.models.causal_chains.chain_so_far import (
    ChainSoFar,
    LinkedHop,
)
from take_home.causal_chains.agents.models.causal_chains.input_variable import InputVariable
from take_home.causal_chains.agents.models.causal_chains.leads_to import LeadsTo
from take_home.causal_chains.agents.models.causal_chains.situation import Situation
from take_home.causal_chains.agents.stores.causal_chain_store.protocol.protocol import (
    CausalChainStore,
)


def _key(
    situation_id: UUID,
    version: int,
) -> tuple[UUID, int]:
    return (situation_id, version)


def _stored_kind(kind: str) -> Literal["start", "situation", "terminal"]:
    if kind == "start" or kind == "situation" or kind == "terminal":
        return kind
    raise ValueError("situation kind is missing")


def _situation_from_graph(
    situation_id: UUID,
    version: int,
    created_timestamp: str,
    title: str,
    desc: str,
    remained_drivers: list[str],
    kind: str,
) -> Situation:
    return Situation(
        situation_id=situation_id,
        version=version,
        kind=_stored_kind(kind),
        created_timestamp=datetime.fromisoformat(created_timestamp),
        title=title,
        desc=desc,
        remained_drivers=remained_drivers,
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
        if situation.kind != "start":
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
            if dest is None or dest.kind == "start":
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
    async def add_case(
        self,
        case: Case,
    ) -> None:
        self._graph_db.merge_case(
            case.case_id,
            case.conversation_id,
            case.from_message_id,
            case.created_timestamp.isoformat(),
            case.updated_timestamp.isoformat(),
        )

    @override
    async def get_case(
        self,
        case_id: UUID,
    ) -> Case:
        found = self._graph_db.get_case(case_id)
        if found is None:
            raise ValueError("case is missing")
        (
            found_id,
            conversation_id,
            from_message_id,
            created_timestamp,
            updated_timestamp,
        ) = found
        return Case(
            case_id=found_id,
            conversation_id=conversation_id,
            from_message_id=from_message_id,
            created_timestamp=datetime.fromisoformat(created_timestamp),
            updated_timestamp=datetime.fromisoformat(updated_timestamp),
        )

    @override
    async def add_situation(
        self,
        case: Case,
        situation: Situation,
    ) -> None:
        self._graph_db.merge_situation(
            situation.situation_id,
            situation.version,
            situation.created_timestamp.isoformat(),
            situation.title,
            situation.desc,
            list(situation.remained_drivers),
            case.case_id,
            situation.kind,
        )

    @override
    async def link_situations(
        self,
        case: Case,
        from_situation: Situation,
        to_situation: Situation,
        link: LeadsTo,
    ) -> None:
        await self.add_situation(case, from_situation)
        await self.add_situation(case, to_situation)
        self._graph_db.merge_leads_to(
            link.from_situation_id,
            link.from_version,
            link.to_situation_id,
            link.to_version,
            link.p,
            [(item.name, item.desc, item.probability) for item in link.inputs],
        )

    @override
    async def lookup_leaf_situations(
        self,
        case: Case,
        start: Situation,
    ) -> list[Situation]:
        return [
            Situation(
                situation_id=situation_id,
                version=version,
                kind="situation",
                created_timestamp=datetime.fromisoformat(created_timestamp),
                title=title,
                desc=desc,
                remained_drivers=remained_drivers,
            )
            for (
                situation_id,
                version,
                created_timestamp,
                title,
                desc,
                remained_drivers,
            ) in self._graph_db.list_leaf_situations(
                case.case_id,
                start.situation_id,
                start.version,
            )
        ]

    @override
    async def reaches_terminal(
        self,
        case: Case,
        start: Situation,
        terminal: Situation,
    ) -> bool:
        return self._graph_db.reaches_terminal(
            case.case_id,
            start.situation_id,
            start.version,
            terminal.situation_id,
            terminal.version,
        )

    @override
    async def lookup_chain_so_far(
        self,
        case: Case,
        start: Situation,
    ) -> ChainSoFar:
        row = self._graph_db.lookup_chain_so_far(
            case.case_id,
            start.situation_id,
            start.version,
        )
        if row is None:
            raise ValueError("start is missing")
        start_row, hop_rows, link_rows = row
        (
            start_id,
            start_version,
            start_created_timestamp,
            start_title,
            start_desc,
            start_remained_drivers,
        ) = start_row
        hops: list[LinkedHop] = []
        for hop_row, link_row in zip(hop_rows, link_rows, strict=True):
            situation_id, version, created_timestamp, title, desc, remained_drivers = hop_row
            (
                from_situation_id,
                from_version,
                to_situation_id,
                to_version,
                p,
                inputs,
            ) = link_row
            hops.append(
                LinkedHop(
                    situation=Situation(
                        situation_id=situation_id,
                        version=version,
                        kind="situation",
                        created_timestamp=datetime.fromisoformat(created_timestamp),
                        title=title,
                        desc=desc,
                        remained_drivers=remained_drivers,
                    ),
                    link=LeadsTo(
                        from_situation_id=from_situation_id,
                        from_version=from_version,
                        to_situation_id=to_situation_id,
                        to_version=to_version,
                        p=p,
                        inputs=[
                            InputVariable(
                                name=name,
                                desc=desc,
                                probability=probability,
                            )
                            for name, desc, probability in inputs
                        ],
                    ),
                )
            )
        return ChainSoFar(
            start=Situation(
                situation_id=start_id,
                version=start_version,
                kind="start",
                created_timestamp=datetime.fromisoformat(start_created_timestamp),
                title=start_title,
                desc=start_desc,
                remained_drivers=start_remained_drivers,
            ),
            hops=hops,
        )

    @override
    async def get_chains(
        self,
    ) -> list[CausalChain]:
        grouped: dict[UUID, list[Situation]] = {}
        for (
            situation_id,
            version,
            created_timestamp,
            title,
            desc,
            remained_drivers,
            kind,
            case_id,
        ) in self._graph_db.list_situations():
            grouped.setdefault(case_id, []).append(
                _situation_from_graph(
                    situation_id,
                    version,
                    created_timestamp,
                    title,
                    desc,
                    remained_drivers,
                    kind,
                )
            )
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
                        desc=desc,
                        probability=probability,
                    )
                    for name, desc, probability in inputs
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
        chains: list[CausalChain] = []
        for case_id, case_situations in grouped.items():
            keys = {
                _key(situation.situation_id, situation.version)
                for situation in case_situations
            }
            case_links = [
                link
                for link in links
                if _key(link.from_situation_id, link.from_version) in keys
                and _key(link.to_situation_id, link.to_version) in keys
            ]
            chains.extend(
                chain.model_copy(update={"case_id": case_id})
                for chain in chains_for(case_situations, case_links)
            )
        return chains
