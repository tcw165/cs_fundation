import asyncio
from types import SimpleNamespace

import take_home.causal_chains.agents.agent_runner.app_agent_runner as app_agent_runner_module
import take_home.causal_chains.agents.eval.offline.offline as offline_module
from take_home.causal_chains.agents.clients.memcache.span_processor import (
    MemcacheSpanProcessor,
)
from take_home.causal_chains.agents.eval.offline.offline import run_offline
from take_home.causal_chains.agents.models.messaging.message import MarkdownMessage


def test_offline_turn_saves_the_user_message_and_prints_runner_messages(
    monkeypatch,
) -> None:
    class _FakeDelta:
        def __init__(self, delta: str) -> None:
            self.delta = delta

    class _FakeResult:
        def stream_events(self):
            async def _events():
                yield SimpleNamespace(
                    type="raw_response_event",
                    data=_FakeDelta("one\n\ntwo"),
                )

            return _events()

        def cancel(self) -> None:
            return None

    seen_include_traces: list[bool] = []

    def run_streamed(
        agent,
        input,
        context=None,
    ):
        seen_include_traces.append(context.run_config.include_traces)
        return _FakeResult()

    monkeypatch.setattr(app_agent_runner_module, "ResponseTextDeltaEvent", _FakeDelta)
    monkeypatch.setattr(
        app_agent_runner_module.Runner,
        "run_streamed",
        run_streamed,
    )

    async def exercise():
        service, events = await run_offline("hormuz")
        messages = await service._messaging_store.list_messages("1")
        return messages, events

    messages, events = asyncio.run(exercise())
    user_messages = [message.text for message in messages if message.role == "user"]
    assert user_messages == ["hormuz"]
    assert [event.text for event in events] == ["one", "two"]
    assert all(isinstance(event, MarkdownMessage) for event in events)
    assert seen_include_traces == [True]


def test_offline_uses_the_api_key_without_a_shell_project(monkeypatch) -> None:
    installed: dict[str, object] = {}

    def capture_client(client: object, use_for_tracing: bool) -> None:
        installed["client"] = client
        installed["tracing"] = use_for_tracing

    def capture_processors(processors: list[object]) -> None:
        installed["processors"] = processors

    class _FakeResult:
        def stream_events(self):
            async def _events():
                if False:
                    yield None

            return _events()

        def cancel(self) -> None:
            return None

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("OPENAI_PROJECT_ID", "proj_stale")
    monkeypatch.setenv("OPENAI_ORG_ID", "org_stale")
    monkeypatch.setattr(offline_module, "set_default_openai_client", capture_client)
    monkeypatch.setattr(offline_module, "set_trace_processors", capture_processors)
    monkeypatch.setattr(
        app_agent_runner_module.Runner,
        "run_streamed",
        lambda agent, input, context=None: _FakeResult(),
    )

    asyncio.run(run_offline("hormuz"))
    client = installed["client"]
    assert client.api_key == "sk-test"
    assert client.project is None
    assert client.organization is None
    assert installed["tracing"] is False
    processors = installed["processors"]
    assert isinstance(processors, list)
    assert len(processors) == 1
    assert isinstance(processors[0], MemcacheSpanProcessor)
