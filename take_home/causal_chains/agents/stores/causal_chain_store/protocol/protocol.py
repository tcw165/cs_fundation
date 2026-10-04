from typing import Protocol, runtime_checkable
from uuid import UUID

from take_home.causal_chains.agents.models.messaging.causal_chain import CausalChain
from take_home.causal_chains.agents.models.causal_chains.case import Case
from take_home.causal_chains.agents.models.causal_chains.chain_so_far import ChainSoFar
from take_home.causal_chains.agents.models.causal_chains.leads_to import LeadsTo
from take_home.causal_chains.agents.models.causal_chains.situation import (
    Situation,
)


@runtime_checkable
class CausalChainStore(Protocol):
    async def add_case(
        self,
        case: Case,
    ) -> None: ...

    async def get_case(
        self,
        case_id: UUID,
    ) -> Case: ...

    async def add_situation(
        self,
        case: Case,
        situation: Situation,
    ) -> None: ...

    async def link_situations(
        self,
        case: Case,
        from_situation: Situation,
        to_situation: Situation,
        link: LeadsTo,
    ) -> None: ...

    async def lookup_leaf_situations(
        self,
        case: Case,
        start: Situation,
    ) -> list[Situation]: ...

    async def reaches_terminal(
        self,
        case: Case,
        start: Situation,
        terminal: Situation,
    ) -> bool: ...

    async def lookup_chain_so_far(
        self,
        case: Case,
        start: Situation,
    ) -> ChainSoFar: ...

    async def get_chains(
        self,
    ) -> list[CausalChain]: ...
