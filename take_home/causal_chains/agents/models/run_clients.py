from dataclasses import dataclass

from take_home.causal_chains.agents.stores.causal_chain_store.protocol.protocol import (
    CausalChainStore,
)
from take_home.causal_chains.agents.stores.messaging_store.protocol.messaging_store import (
    MessagingStore,
)


@dataclass
class RunClients:
    causal_chain_store: CausalChainStore
    messaging_store: MessagingStore | None = None
