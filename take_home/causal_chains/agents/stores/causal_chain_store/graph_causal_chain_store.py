from typing import override

from take_home.causal_chains.agents.clients.graph_db.protocol.protocol import GraphDb
from take_home.causal_chains.agents.models.causal_chains.leads_to import LeadsTo
from take_home.causal_chains.agents.models.causal_chains.situation import Situation
from take_home.causal_chains.agents.stores.causal_chain_store.protocol.protocol import (
    CausalChainStore,
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
            situation.desc,
            situation.is_root,
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
            link.to_situation_id,
            link.p,
        )
