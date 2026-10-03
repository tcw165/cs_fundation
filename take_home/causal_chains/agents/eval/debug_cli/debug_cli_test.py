import asyncio
import threading

import anyio
import httpx
from click.testing import CliRunner
from dependency_injector import providers

from take_home.causal_chains.agents.di.container import AppContainer
from take_home.causal_chains.agents.endpoints import conversation
from take_home.causal_chains.agents.eval.debug_cli.debug_cli import main
from take_home.causal_chains.agents.main_app import create_app
from take_home.causal_chains.agents.stub_runner.stub_turn_runner import StubTurnRunner


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
        limit: int,
        exclusive_start_sk: str | None = None,
    ) -> tuple[list[dict[str, object]], str | None]:
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


class _SyncAsgiTransport(httpx.BaseTransport):
    def __init__(self, app: object) -> None:
        self._app = app
        self.requests: list[httpx.Request] = []
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._loop.run_forever, daemon=True)
        self._thread.start()

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
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


def test_query_hello_prints_markdown_and_done(monkeypatch):
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
    container.clients.dynamo_db.override(providers.Object(_FakeDynamoDb()))
    transport = _SyncAsgiTransport(create_app(container))
    original_client = httpx.Client

    def client_for_app(*args, **kwargs):
        return original_client(transport=transport, base_url="http://test")

    monkeypatch.setattr(
        "take_home.causal_chains.agents.eval.debug_cli.debug_cli.httpx.Client",
        client_for_app,
    )
    result = CliRunner().invoke(
        main,
        ["--query", "hello"],
    )
    assert result.exit_code == 0
    assert "received user message" in result.output
    assert "queued turn" in result.output
    assert "streamed message kind=markdown" in result.output
    assert "echo: hello" in result.output
    sse_requests = [
        request
        for request in transport.requests
        if request.url.path.endswith("/sse")
    ]
    assert sse_requests[-1].url.params["after_message"]
    assert sse_requests[-1].url.params["after_message_timestamp"]


def test_stream_echoes_each_chunk_before_the_next_read(monkeypatch):
    chunks = [
        "event: delta\ndata: {\"text\":\"oil\"}\n\n",
        "event: done\ndata: {\"message_id\":\"m_1\"}\n\n",
    ]
    echoed: list[str] = []

    class _Response:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            return {
                "turn": {"turn_id": "t_1", "from_message": "m_1"},
                    "received_message": {
                        "kind": "markdown",
                        "text": "hello",
                        "created_timestamp": "2026-09-30T00:00:00+00:00",
                    },
            }

        def iter_text(self):
            for index, chunk in enumerate(chunks):
                assert echoed == chunks[:index]
                yield chunk

    class _Stream:
        def __enter__(self) -> _Response:
            return _Response()

        def __exit__(self, *args: object) -> bool:
            return False

    class _Client:
        def __enter__(self) -> "_Client":
            return self

        def __exit__(self, *args: object) -> bool:
            return False

        def post(self, *args: object, **kwargs: object) -> _Response:
            return _Response()

        def stream(self, *args: object, **kwargs: object) -> _Stream:
            return _Stream()

    monkeypatch.setattr(
        "take_home.causal_chains.agents.eval.debug_cli.debug_cli.httpx.Client",
        lambda *args, **kwargs: _Client(),
    )
    monkeypatch.setattr(
        "take_home.causal_chains.agents.eval.debug_cli.debug_cli.click.echo",
        lambda text, nl=True: echoed.append(text),
    )
    result = CliRunner().invoke(main, ["--query", "hello"])
    assert result.exit_code == 0
    assert echoed == chunks
