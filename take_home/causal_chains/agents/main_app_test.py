import json
from types import SimpleNamespace

from fastapi.testclient import TestClient

from take_home.causal_chains.agents.di.container import AppContainer
from take_home.causal_chains.agents.main_app import create_app


def test_health_reports_ready():
    client = TestClient(create_app(AppContainer()))
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_post_message_and_sse_with_stub_runner():
    container = AppContainer()
    container.config.agent_runner.from_value("stub")
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


def test_app_runner_and_span_processor_share_memcache():
    container = AppContainer()
    container.config.openai_api_key.from_value("test")
    container.config.agent_runner.from_value("openai")
    runner = container.agent_runner()
    container.clients().span_processor().on_span_end(
        SimpleNamespace(export=lambda: {"name": "now_scout"})
    )
    assert runner._memcache.flush() == json.dumps({"name": "now_scout"}) + "\n"
