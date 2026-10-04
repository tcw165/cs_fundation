import asyncio
import json
import logging
import threading
from types import SimpleNamespace
from uuid import UUID

import httpx
from dependency_injector import providers
from fastapi.testclient import TestClient

from take_home.causal_chains.agents.di.container import AppContainer
from take_home.causal_chains.agents.endpoints import conversation
from take_home.causal_chains.agents.main_app import create_app
from take_home.causal_chains.agents.stub_runner.stub_turn_runner import StubTurnRunner
from take_home.causal_chains.agents.observability.endpoint_logging.endpoint_logging import (
    SkipPollingEndpointPaths,
)
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

    def delete_item(self, table_name: str, key: dict[str, object]) -> None:
        stored_key = tuple(sorted(key.items()))
        self._items.pop((table_name, stored_key), None)

    def query(
        self,
        table_name: str,
        key_name: str,
        key_value: str,
        sk_name: str,
        sk_prefix: str,
        limit: int,
        exclusive_start_sk: str | None = None,
    ) -> tuple[list[dict[str, object]], str | None]:
        if limit < 1:
            raise ValueError("limit is at least 1")
        rows = [
            item
            for (stored_table, _), item in self._items.items()
            if stored_table == table_name
            and item.get(key_name) == key_value
            and str(item.get(sk_name, "")).startswith(sk_prefix)
        ]
        rows.sort(key=lambda row: str(row.get(sk_name, "")))
        if exclusive_start_sk is not None:
            rows = [
                row
                for row in rows
                if str(row.get(sk_name, "")) > exclusive_start_sk
            ]
        page = rows[:limit]
        if len(page) < limit or not page:
            return page, None
        return page, str(page[-1][sk_name])

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


def test_get_messages_rejects_a_limit_outside_1_to_100():
    container = AppContainer()
    container.causal_chain_store.override(providers.Object(object()))
    _override_dynamo_db(container)
    client = TestClient(create_app(container))
    assert client.get("/api/v1/conversation/1/messages", params={"limit": 0}).status_code == 422
    assert client.get("/api/v1/conversation/1/messages", params={"limit": 101}).status_code == 422
    assert client.get("/api/v1/conversation/1/messages", params={"limit": 100}).status_code == 200


def test_post_message_rejects_text_outside_the_length_bounds():
    container = AppContainer()
    container.config.agent_runner.from_value("stub")
    container.config.user_uuid.from_value("user-1")
    container.causal_chain_store.override(providers.Object(object()))
    _override_dynamo_db(container)
    client = TestClient(create_app(container))
    empty = client.post("/api/v1/conversation/1/messages", json={"text": ""})
    oversized = client.post(
        "/api/v1/conversation/1/messages",
        json={"text": "a" * 10_000},
    )
    assert empty.status_code == 422
    assert oversized.status_code == 422
    stored = asyncio.run(container.messaging_store().list_messages("1", 20)).messages
    assert stored == []


class _OpenStreamTransport(httpx.BaseTransport):
    """Returns the HTTP body before Starlette background tasks finish.

    The stub turn stays blocked until the stream loads the turn, so a later
    SSE request still sees a live turn.
    """

    def __init__(self, app: object) -> None:
        self._app = app
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._loop.run_forever, daemon=True)
        self._thread.start()

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        future = asyncio.run_coroutine_threadsafe(self._send(request), self._loop)
        return future.result(timeout=10)

    async def _send(self, request: httpx.Request) -> httpx.Response:
        scope = {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": request.method,
            "headers": [(key.lower(), value) for key, value in request.headers.raw],
            "scheme": request.url.scheme,
            "path": request.url.path,
            "raw_path": request.url.raw_path.split(b"?")[0],
            "query_string": request.url.query,
            "server": (request.url.host, request.url.port),
            "client": ("127.0.0.1", 123),
            "root_path": "",
        }
        sent = False
        status_code: int | None = None
        response_headers: list[tuple[bytes, bytes]] | None = None
        body_parts: list[bytes] = []
        response_complete = asyncio.Event()

        async def receive() -> dict[str, object]:
            nonlocal sent
            if sent:
                await response_complete.wait()
                return {"type": "http.disconnect"}
            sent = True
            return {"type": "http.request", "body": request.content, "more_body": False}

        async def send(message: dict[str, object]) -> None:
            nonlocal status_code, response_headers
            if message["type"] == "http.response.start":
                status_code = int(message["status"])
                response_headers = list(message.get("headers", []))
                return
            if message["type"] != "http.response.body":
                return
            chunk = message.get("body", b"")
            if isinstance(chunk, bytes) and chunk:
                body_parts.append(chunk)
            if not message.get("more_body", False):
                response_complete.set()

        task = asyncio.create_task(self._app(scope, receive, send))
        task.add_done_callback(
            lambda done: response_complete.set() if not response_complete.is_set() else None,
        )
        await response_complete.wait()
        if task.done() and task.exception() is not None and status_code is None:
            task.result()
        assert status_code is not None
        return httpx.Response(
            status_code=status_code,
            headers=response_headers or [],
            content=b"".join(body_parts),
        )


def test_post_message_and_sse_with_stub_runner(monkeypatch):
    release_runner = threading.Event()
    original_stream = StubTurnRunner.stream
    original_require = conversation._require

    async def wait_for_the_stream(self, inputs, context):
        await asyncio.to_thread(release_runner.wait)
        return await original_stream(self, inputs, context)

    async def require_then_release(*args, **kwargs):
        turn = await original_require(*args, **kwargs)
        release_runner.set()
        return turn

    monkeypatch.setattr(StubTurnRunner, "stream", wait_for_the_stream)
    monkeypatch.setattr(conversation, "_require", require_then_release)
    container = AppContainer()
    container.config.agent_runner.from_value("stub")
    container.config.user_uuid.from_value("user-1")
    container.causal_chain_store.override(providers.Object(object()))
    _override_dynamo_db(container)
    client = httpx.Client(
        transport=_OpenStreamTransport(create_app(container)),
        base_url="http://test",
    )
    created = client.post("/api/v1/conversation/1/messages", json={"text": "hello"})
    assert created.status_code == 200
    body = created.json()
    assert body["turn"]["status"] == "queued"
    assert body["received_message"]["text"] == "hello"
    turn_id = body["turn"]["turn_id"]
    stream = client.get(
        f"/api/v1/conversation/1/turn/{turn_id}/sse",
        params={
            "after_message": body["turn"]["from_message"],
            "after_message_timestamp": body["received_message"]["created_timestamp"],
        },
    )
    assert stream.status_code == 200
    assert "echo: hello" in stream.text
    assert "event: conversation_messages" in stream.text
    stored = asyncio.run(container.messaging_store().list_messages("1", 20)).messages
    assert {message.text for message in stored} == {"hello", "echo: hello"}


def test_get_causal_chains_returns_the_stored_chains():
    root = StartSituation(
        situation_id=UUID("11111111-1111-4111-8111-111111111111"),
        version=1,
        title="now",
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
    response = client.get("/api/v1/causal_chains")
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


def test_main_installs_one_polling_access_filter(monkeypatch):
    monkeypatch.delenv("BRAINTRUST_ORGANIZATION_NAME", raising=False)
    monkeypatch.setenv("BRAINTRUST_API_KEY", "")
    monkeypatch.setenv("BRAINTRUST_PROJECT_ID", "")
    _invoke_main(monkeypatch)
    _invoke_main(monkeypatch)
    access = logging.getLogger("uvicorn.access")
    installed = [
        item
        for item in access.filters
        if isinstance(item, SkipPollingEndpointPaths)
    ]
    assert len(installed) == 1
