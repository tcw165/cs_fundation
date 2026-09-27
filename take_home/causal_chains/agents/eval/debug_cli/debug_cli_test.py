import anyio
import asyncio
import httpx
from dependency_injector import providers

from take_home.causal_chains.agents.eval.debug_cli.debug_cli import post_and_read
from take_home.causal_chains.agents.di.container import AppContainer
from take_home.causal_chains.agents.main_app import create_app


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


class _SyncAsgiTransport(httpx.BaseTransport):
    def __init__(self, app: object) -> None:
        self._transport = httpx.ASGITransport(app=app)

    def handle_request(self, request: httpx.Request) -> httpx.Response:
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


def test_post_and_read_stub_prints_delta_and_done():
    container = AppContainer()
    container.config.agent_runner.from_value("stub")
    container.clients.dynamo_db.override(providers.Object(_FakeDynamoDb()))
    transport = _SyncAsgiTransport(create_app(container))
    with httpx.Client(transport=transport, base_url="http://test") as client:
        body = post_and_read("http://test", "1", "hello", client)
    assert "event: delta" in body
    assert "event: done" in body
    stored = asyncio.run(container.messaging_store().list_messages("1"))
    assert len(stored) == 1
    assert stored[0].text == "hello"
