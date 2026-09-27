import json
from types import SimpleNamespace

import take_home.causal_chains.agents.clients.di.container as container_module
from take_home.causal_chains.agents.clients.di.container import ClientsContainer
from take_home.causal_chains.agents.clients.dynamo_db.protocol.protocol import DynamoDb
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


def test_dynamo_db_singleton_is_a_dynamo_db(monkeypatch):
    def fake_client(service_name: str, **kwargs: object) -> object:
        assert service_name == "dynamodb"
        return object()

    monkeypatch.setattr(container_module.boto3, "client", fake_client)
    container = ClientsContainer()
    first = container.dynamo_db()
    second = container.dynamo_db()
    assert isinstance(first, DynamoDb)
    assert first is second


def test_memcache_singleton_appends_and_flushes():
    container = ClientsContainer()
    first = container.memcache()
    second = container.memcache()
    assert first is second
    first.append("span\n")
    first.append("more\n")
    assert first.flush() == "span\nmore\n"
    assert second.flush() == ""


def test_span_processor_writes_to_the_memcache_singleton():
    container = ClientsContainer()
    processor = container.span_processor()
    assert processor is container.span_processor()
    processor.on_span_end(SimpleNamespace(export=lambda: {"name": "now_scout"}))
    assert container.memcache().flush() == json.dumps({"name": "now_scout"}) + "\n"
