from typing import override

from take_home.causal_chains.agents.clients.dynamo_db.protocol.protocol import DynamoDb
from take_home.causal_chains.agents.models.causal_chains.chain_graph import ChainGraph
from take_home.causal_chains.agents.stores.causal_chain_store.protocol.protocol import (
    CausalChainStore,
)


class DdbCausalChainStore(CausalChainStore):
    def __init__(self, dynamo_db: DynamoDb) -> None:
        self._dynamo_db = dynamo_db

    @override
    def put_chain(self, turn_id: str, chain: ChainGraph) -> None:
        item = chain.model_dump(mode="json")
        item["turn_id"] = turn_id
        self._dynamo_db.put_item("causal_chain", item)

    @override
    def get_chain(self, turn_id: str) -> ChainGraph | None:
        item = self._dynamo_db.get_item("causal_chain", {"turn_id": turn_id})
        if item is None:
            return None
        return ChainGraph.model_validate(item)
