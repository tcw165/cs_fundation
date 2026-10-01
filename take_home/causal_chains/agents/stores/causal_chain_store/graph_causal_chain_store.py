from collections import deque
from datetime import datetime
from typing import override
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
from take_home.causal_chains.agents.models.causal_chains.situation import (
    Situation,
    StartSituation,
    TerminalSituation,
)
from take_home.causal_chains.agents.stores.causal_chain_store.protocol.protocol import (
    CausalChainStore,
)


def _key(
    situation_id: UUID,
    version: int,
) -> tuple[UUID, int]:
    return (situation_id, version)


def _kind(situation: Situation) -> str:
    if isinstance(situation, StartSituation):
        return "start"
    if isinstance(situation, TerminalSituation):
        return "terminal"
    return "situation"


def _factors(situation: Situation) -> list[str]:
    if isinstance(situation, StartSituation):
        return list(situation.potential_factors)
    return []


def _ask(situation: Situation) -> str:
    if isinstance(situation, TerminalSituation):
        return situation.original_ask
    return ""


def _situation_from_graph(
    situation_id: UUID,
    version: int,
    desc: str,
    kind: str,
    potential_factors: list[str],
    original_ask: str,
) -> Situation:
    if kind == "start":
        return StartSituation(
            situation_id=situation_id,
            version=version,
            desc=desc,
            potential_factors=potential_factors,
        )
    if kind == "terminal":
        return TerminalSituation(
            situation_id=situation_id,
            version=version,
            desc=desc,
            original_ask=original_ask,
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
    async def add_case(
        self,
        case: Case,
    ) -> None:
        self._graph_db.merge_case(
            case.case_id,
            case.conversation_id,
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
        found_id, conversation_id, created_timestamp, updated_timestamp = found
        return Case(
            case_id=found_id,
            conversation_id=conversation_id,
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
            situation.desc,
            case.case_id,
            _kind(situation),
            _factors(situation),
            _ask(situation),
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
            [(item.name, item.value) for item in link.inputs],
        )

    @override
    async def lookup_leaf_situations(
        self,
        case: Case,
        start: StartSituation,
    ) -> list[Situation]:
        return [
            Situation(
                situation_id=situation_id,
                version=version,
                desc=desc,
            )
            for situation_id, version, desc in self._graph_db.list_leaf_situations(
                case.case_id,
                start.situation_id,
                start.version,
            )
        ]

    @override
    async def reaches_terminal(
        self,
        case: Case,
        start: StartSituation,
        terminal: TerminalSituation,
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
        start: StartSituation,
    ) -> ChainSoFar:
        row = self._graph_db.lookup_chain_so_far(
            case.case_id,
            start.situation_id,
            start.version,
        )
        if row is None:
            raise ValueError("start is missing")
        start_row, hop_rows, link_rows = row
        start_id, start_version, start_desc, factors = start_row
        hops: list[LinkedHop] = []
        for hop_row, link_row in zip(hop_rows, link_rows, strict=True):
            situation_id, version, desc = hop_row
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
                        desc=desc,
                    ),
                    link=LeadsTo(
                        from_situation_id=from_situation_id,
                        from_version=from_version,
                        to_situation_id=to_situation_id,
                        to_version=to_version,
                        p=p,
                        inputs=[
                            InputVariable(name=name, value=value)
                            for name, value in inputs
                        ],
                    ),
                )
            )
        return ChainSoFar(
            start=StartSituation(
                situation_id=start_id,
                version=start_version,
                desc=start_desc,
                potential_factors=factors,
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
            desc,
            kind,
            potential_factors,
            original_ask,
            case_id,
        ) in self._graph_db.list_situations():
            grouped.setdefault(case_id, []).append(
                _situation_from_graph(
                    situation_id,
                    version,
                    desc,
                    kind,
                    potential_factors,
                    original_ask,
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
