import anyio
import httpx
from click.testing import CliRunner
from dependency_injector import providers

from take_home.causal_chains.agents.di.container import AppContainer
from take_home.causal_chains.agents.eval.debug_cli.debug_cli import main
from take_home.causal_chains.agents.main_app import create_app


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
        self._transport = httpx.ASGITransport(app=app)
        self.requests: list[httpx.Request] = []

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)

        async def send() -> httpx.Response:
            response = await self._transport.handle_async_request(request)
            body = await response.aread()
            await response.aclose()
            return httpx.Response(
                status_code=response.status_code,
                headers=response.headers,
                content=body,
            )

        return anyio.run(send)


def test_query_hello_prints_markdown_and_done(monkeypatch):
    container = AppContainer()
    container.config.agent_runner.from_value("stub")
    container.config.user_uuid.from_value("user-1")
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
    assert "event: markdown" in result.output
    sse_requests = [
        request
        for request in transport.requests
        if request.url.path.endswith("/sse")
    ]
    assert sse_requests[-1].url.params["include_traces"] == "true"
    assert sse_requests[-1].url.params["after_message"]


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
                "received_message": {"kind": "markdown", "text": "hello"},
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
