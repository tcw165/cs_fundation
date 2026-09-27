import anyio
import httpx

from take_home.causal_chains.agents.chat_client.chat_client import post_and_read
from take_home.causal_chains.agents.di.container import AppContainer
from take_home.causal_chains.agents.main_app import create_app


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
    transport = _SyncAsgiTransport(create_app(container))
    with httpx.Client(transport=transport, base_url="http://test") as client:
        body = post_and_read("http://test", "1", "hello", client)
    assert "event: delta" in body
    assert "event: done" in body
