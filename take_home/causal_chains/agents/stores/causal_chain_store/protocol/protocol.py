from typing import Protocol, runtime_checkable

from take_home.causal_chains.agents.models.causal_chains.chain_graph import ChainGraph


@runtime_checkable
class CausalChainStore(Protocol):
    def put_chain(self, turn_id: str, chain: ChainGraph) -> None: ...

    def get_chain(self, turn_id: str) -> ChainGraph | None: ...
