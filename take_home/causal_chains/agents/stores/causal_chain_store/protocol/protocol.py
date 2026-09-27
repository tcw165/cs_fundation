from typing import Protocol, runtime_checkable

from take_home.causal_chains.agents.models.causal_chains.leads_to import LeadsTo
from take_home.causal_chains.agents.models.causal_chains.situation import Situation


@runtime_checkable
class CausalChainStore(Protocol):
    async def add_situation(
        self,
        situation: Situation,
    ) -> None: ...

    async def link_situations(
        self,
        from_situation: Situation,
        to_situation: Situation,
        link: LeadsTo,
    ) -> None: ...
