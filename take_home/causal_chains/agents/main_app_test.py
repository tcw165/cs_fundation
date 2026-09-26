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


def test_health_reports_down_when_override_fails():
    container = AppContainer()
    with container.db_ping.override(providers.Object(False)):
        client = TestClient(create_app(container))
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "db": "down"}
