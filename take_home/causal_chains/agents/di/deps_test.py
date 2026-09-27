import pytest
from dependency_injector import providers

from take_home.causal_chains.agents.di.container import AppContainer
from take_home.causal_chains.agents.di.deps import get_app_container
from take_home.causal_chains.agents.stores.causal_chain_store.protocol.protocol import (
    CausalChainStore,
)


class _FakeGraphDb:
    pass


def test_get_app_container_raises_when_unbound():
    with pytest.raises(RuntimeError, match="AppContainer not bound"):
        get_app_container()


def test_causal_chain_store_is_a_causal_chain_store():
    container = AppContainer()
    container.clients.graph_db.override(providers.Object(_FakeGraphDb()))
    store = container.causal_chain_store()
    assert isinstance(store, CausalChainStore)
