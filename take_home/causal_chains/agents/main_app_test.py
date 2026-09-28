import asyncio
import json
from types import SimpleNamespace
from uuid import UUID

from dependency_injector import providers
from fastapi.testclient import TestClient

from take_home.causal_chains.agents.di.container import AppContainer
from take_home.causal_chains.agents.main_app import create_app
from take_home.causal_chains.agents.models.messaging.causal_chain import CausalChain
from take_home.causal_chains.agents.models.causal_chains.situation import Situation


class _FakeDynamoDb:
    def __init__(self) -> None:
        self._items: dict[tuple[str, tuple[tuple[str, object], ...]], dict[str, object]] = {}
        self.put_item("conversation", {"conversation_id": "1", "messages": []})

    def put_item(self, table_name: str, item: dict[str, object]) -> None:
        if table_name == "turn":
            key = (("turn_id", item["turn_id"]),)
        else:
            key = (("conversation_id", item["conversation_id"]),)
        self._items[(table_name, key)] = item

    def get_item(self, table_name: str, key: dict[str, object]) -> dict[str, object] | None:
        stored_key = tuple(sorted(key.items()))
        return self._items.get((table_name, stored_key))


def _override_dynamo_db(container: AppContainer) -> None:
    container.clients.dynamo_db.override(providers.Object(_FakeDynamoDb()))


def test_health_reports_ready():
    client = TestClient(create_app(AppContainer()))
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_post_message_and_sse_with_stub_runner():
    container = AppContainer()
    container.config.agent_runner.from_value("stub")
    _override_dynamo_db(container)
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
    stored = asyncio.run(container.messaging_store().list_messages("1"))
    assert len(stored) == 1
    assert stored[0].text == "hello"


def test_get_causal_chains_returns_the_stored_chains():
    root = Situation(
        situation_id=UUID("11111111-1111-4111-8111-111111111111"),
        version=1,
        desc="now",
        is_root=True,
    )
    chain = CausalChain(situations=[root], links=[])

    class _Chains:
        async def get_chains(
            self,
        ) -> list[CausalChain]:
            return [chain]

    container = AppContainer()
    container.causal_chain_store.override(providers.Object(_Chains()))
    client = TestClient(create_app(container))
    response = client.get("/causal_chains")
    assert response.status_code == 200
    assert response.json() == [chain.model_dump(mode="json")]


def test_app_runner_and_span_processor_share_memcache():
    container = AppContainer()
    container.config.openai_api_key.from_value("test")
    container.config.agent_runner.from_value("openai")
    runner = container.agent_runner()
    container.clients().span_processor().on_span_end(
        SimpleNamespace(export=lambda: {"name": "now_scout"})
    )
    assert runner._memcache.flush() == json.dumps({"name": "now_scout"}) + "\n"
