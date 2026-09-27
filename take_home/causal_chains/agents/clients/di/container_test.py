import take_home.causal_chains.agents.clients.di.container as container_module
from take_home.causal_chains.agents.clients.di.container import ClientsContainer
from take_home.causal_chains.agents.clients.graph_db.protocol.protocol import GraphDb


def test_graph_db_singleton_is_a_graph_db(monkeypatch):
    def fake_driver(uri: str, auth: tuple[str, str]):
        return object()

    monkeypatch.setattr(container_module.GraphDatabase, "driver", fake_driver)
    container = ClientsContainer()
    first = container.graph_db()
    second = container.graph_db()
    assert isinstance(first, GraphDb)
    assert first is second
