import asyncio
import json
from types import SimpleNamespace
from uuid import UUID

from dependency_injector import providers
from fastapi.testclient import TestClient

from take_home.causal_chains.agents.di.container import AppContainer
from take_home.causal_chains.agents.main_app import create_app
from take_home.causal_chains.agents.models.messaging.causal_chain import CausalChain
from take_home.causal_chains.agents.models.causal_chains.situation import StartSituation


class _FakeDynamoDb:
    def __init__(self) -> None:
        self._items: dict[tuple[str, tuple[tuple[str, object], ...]], dict[str, object]] = {}

    def put_item(self, table_name: str, item: dict[str, object]) -> None:
        if table_name == "turn":
            key = (("turn_id", item["turn_id"]),)
        else:
            key = (("PK", item["PK"]), ("SK", item["SK"]))
        self._items[(table_name, key)] = item

    def get_item(self, table_name: str, key: dict[str, object]) -> dict[str, object] | None:
        stored_key = tuple(sorted(key.items()))
        return self._items.get((table_name, stored_key))

    def query(
        self,
        table_name: str,
        key_name: str,
        key_value: str,
        sk_name: str,
        sk_prefix: str,
    ) -> list[dict[str, object]]:
        rows = [
            item
            for (stored_table, _), item in self._items.items()
            if stored_table == table_name
            and item.get(key_name) == key_value
            and str(item.get(sk_name, "")).startswith(sk_prefix)
        ]
        rows.sort(key=lambda row: str(row.get(sk_name, "")))
        return rows

    def query_index(
        self,
        table_name: str,
        index_name: str,
        key_name: str,
        key_value: str,
    ) -> list[dict[str, object]]:
        return [
            item
            for (stored_table, _), item in self._items.items()
            if stored_table == table_name and item.get(key_name) == key_value
        ]


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
    container.config.user_uuid.from_value("user-1")
    _override_dynamo_db(container)
    client = TestClient(create_app(container))
    created = client.post("/conversation/1/messages", json={"text": "hello"})
    assert created.status_code == 200
    body = created.json()
    assert body["status"] == "queued"
    assert body["from_message"]
    turn_id = body["turn_id"]
    missing = client.get(f"/conversation/1/turn/{turn_id}/sse")
    assert missing.status_code == 422
    stream = client.get(
        f"/conversation/1/turn/{turn_id}/sse",
        params={"after_message": body["from_message"]},
    )
    assert stream.status_code == 200
    assert "event: markdown" in stream.text
    stored = asyncio.run(container.messaging_store().list_messages("1"))
    assert len(stored) == 1
    assert stored[0].text == "hello"


def test_get_causal_chains_returns_the_stored_chains():
    root = StartSituation(
        situation_id=UUID("11111111-1111-4111-8111-111111111111"),
        version=1,
        desc="now",
        potential_factors=[],
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


def _invoke_main(monkeypatch) -> tuple[list[dict[str, object]], list[list[object]]]:
    import take_home.causal_chains.agents.main as main_module

    inits: list[dict[str, object]] = []
    processor_lists: list[list[object]] = []

    def fake_init_logger(**kwargs: object) -> object:
        inits.append(kwargs)
        return object()

    monkeypatch.setattr(main_module, "init_logger", fake_init_logger)
    monkeypatch.setattr(
        main_module,
        "BraintrustTracingProcessor",
        lambda logger: ("braintrust", logger),
    )
    monkeypatch.setattr(
        main_module,
        "set_trace_processors",
        processor_lists.append,
    )
    monkeypatch.setattr(main_module.uvicorn, "run", lambda *args, **kwargs: None)
    main_module.main.callback("127.0.0.1", 8000)
    return inits, processor_lists


def test_omits_braintrust_when_either_env_var_is_missing(monkeypatch):
    monkeypatch.delenv("BRAINTRUST_ORGANIZATION_NAME", raising=False)
    for api_key, project_id in (("", ""), ("sk-test", ""), ("", "proj_123")):
        monkeypatch.setenv("BRAINTRUST_API_KEY", api_key)
        monkeypatch.setenv("BRAINTRUST_PROJECT_ID", project_id)
        inits, processor_lists = _invoke_main(monkeypatch)
        assert inits == []
        assert len(processor_lists) == 1
        assert len(processor_lists[0]) == 1
        inits.clear()
        processor_lists.clear()


def test_registers_braintrust_when_key_and_project_id_are_set(monkeypatch):
    monkeypatch.setenv("BRAINTRUST_API_KEY", "sk-test")
    monkeypatch.setenv("BRAINTRUST_PROJECT_ID", "proj_123")
    monkeypatch.setenv("BRAINTRUST_ORGANIZATION_NAME", "")
    inits, processor_lists = _invoke_main(monkeypatch)
    assert inits == [
        {
            "project": "causal_chains",
            "project_id": "proj_123",
            "api_key": "sk-test",
            "org_name": None,
        }
    ]
    assert len(processor_lists) == 1
    processors = processor_lists[0]
    assert len(processors) == 2
    assert processors[1][0] == "braintrust"


def test_passes_braintrust_organization_name(monkeypatch):
    monkeypatch.setenv("BRAINTRUST_API_KEY", "sk-test")
    monkeypatch.setenv("BRAINTRUST_PROJECT_ID", "proj_123")
    monkeypatch.setenv("BRAINTRUST_ORGANIZATION_NAME", "acme")
    inits, processor_lists = _invoke_main(monkeypatch)
    assert inits == [
        {
            "project": "causal_chains",
            "project_id": "proj_123",
            "api_key": "sk-test",
            "org_name": "acme",
        }
    ]
    assert len(processor_lists) == 1
    assert len(processor_lists[0]) == 2


def test_app_runner_and_span_processor_share_memcache():
    container = AppContainer()
    container.config.openai_api_key.from_value("test")
    container.config.agent_runner.from_value("openai")
    runner = container.agent_runner()
    container.clients().span_processor().on_span_end(
        SimpleNamespace(export=lambda: {"name": "now_scout"})
    )
    assert runner._memcache.flush() == json.dumps({"name": "now_scout"}) + "\n"
