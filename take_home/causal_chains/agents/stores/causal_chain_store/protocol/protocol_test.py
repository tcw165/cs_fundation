from uuid import UUID

from take_home.causal_chains.agents.models.causal_chains.chain_graph import ChainGraph
from take_home.causal_chains.agents.models.causal_chains.situation import Situation
from take_home.causal_chains.agents.stores.causal_chain_store.protocol.protocol import (
    CausalChainStore,
)

NOW_ID = UUID("11111111-1111-4111-8111-111111111111")


class _Both:
    def __init__(self) -> None:
        self._chains: dict[str, ChainGraph] = {}

    def put_chain(self, turn_id: str, chain: ChainGraph) -> None:
        self._chains[turn_id] = chain

    def get_chain(self, turn_id: str) -> ChainGraph | None:
        return self._chains.get(turn_id)


class _PutOnly:
    def put_chain(self, turn_id: str, chain: ChainGraph) -> None:
        return None


def test_causal_chain_store_requires_put_and_get():
    assert isinstance(_Both(), CausalChainStore)
    assert not isinstance(_PutOnly(), CausalChainStore)


def test_causal_chain_store_round_trips_a_chain():
    store = _Both()
    chain = ChainGraph(
        situations=[Situation(situation_id=NOW_ID, desc="now", is_root=True)],
        edges=[],
        destination_ids=[],
    )
    store.put_chain("t_1", chain)
    assert store.get_chain("t_1") == chain
    assert store.get_chain("missing") is None
