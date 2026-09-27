from uuid import UUID

from take_home.causal_chains.agents.models.causal_chains.chain_graph import ChainGraph
from take_home.causal_chains.agents.models.causal_chains.situation import Situation
from take_home.causal_chains.agents.stores.causal_chain_store.ddb_causal_chain_store import (
    DdbCausalChainStore,
)

NOW_ID = UUID("11111111-1111-4111-8111-111111111111")


class _FakeDynamoDb:
    def __init__(self) -> None:
        self.items: dict[str, dict[str, object]] = {}

    def put_item(self, table_name: str, item: dict[str, object]) -> None:
        assert table_name == "causal_chain"
        self.items[str(item["turn_id"])] = item

    def get_item(self, table_name: str, key: dict[str, object]) -> dict[str, object] | None:
        assert table_name == "causal_chain"
        return self.items.get(str(key["turn_id"]))


def test_put_chain_round_trips_a_one_node_chain():
    database = _FakeDynamoDb()
    store = DdbCausalChainStore(database)
    chain = ChainGraph(
        situations=[Situation(situation_id=NOW_ID, desc="now", is_root=True)],
        edges=[],
        destination_ids=[],
    )
    store.put_chain("t_1", chain)
    stored = database.items["t_1"]
    situations = stored["situations"]
    assert isinstance(situations, list)
    assert situations[0]["situation_id"] == str(NOW_ID)
    assert stored["turn_id"] == "t_1"
    loaded = store.get_chain("t_1")
    assert loaded == chain
    assert loaded is not None
    assert loaded.situations[0].situation_id == NOW_ID
    assert store.get_chain("missing") is None
