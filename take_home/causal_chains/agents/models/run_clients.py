from dataclasses import dataclass

from take_home.causal_chains.agents.stores.causal_chain_store.protocol.protocol import (
    CausalChainStore,
)


@dataclass
class RunClients:
    causal_chain_store: CausalChainStore
