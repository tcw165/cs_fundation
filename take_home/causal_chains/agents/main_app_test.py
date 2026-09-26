from dependency_injector import providers
from fastapi.testclient import TestClient

from take_home.causal_chains.agents.di.container import AppContainer
from take_home.causal_chains.agents.main_app import create_app


def test_health_uses_injected_container_db_ping():
    container = AppContainer()
    with container.db_ping.override(providers.Object(True)):
        client = TestClient(create_app(container))
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "db": "up"}


def test_post_message_and_sse_with_stub_runner():
    container = AppContainer()
    container.config.turn_runner.from_value("stub")
    with container.db_ping.override(providers.Object(True)):
        client = TestClient(create_app(container))
        created = client.post("/conversation/1/messages", json={"text": "hello"})
        assert created.status_code == 200
        body = created.json()
        assert body["status"] == "queued"
        turn_id = body["turn_id"]
        stream = client.get(f"/conversation/1/turn/{turn_id}/sse")
    assert stream.status_code == 200
    assert "event: delta" in stream.text
    assert "event: done" in stream.text


def test_health_reports_down_when_override_fails():
    container = AppContainer()
    with container.db_ping.override(providers.Object(False)):
        client = TestClient(create_app(container))
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "db": "down"}
