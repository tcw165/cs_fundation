import asyncio
from types import SimpleNamespace
from uuid import UUID

import anyio

import take_home.causal_chains.agents.agent_runner.app_agent_runner as app_agent_runner_module
from take_home.causal_chains.agents.agent_runner.app_agent_runner import AppAgentRunner
from take_home.causal_chains.agents.agents.causal_chain.causal_chain import (
    causal_chain,
)
from take_home.causal_chains.agents.clients.memcache.memcache import InMemoryMemcache
from take_home.causal_chains.agents.models.messaging.deeplink_card import DeeplinkCard
from take_home.causal_chains.agents.models.messaging.sse_event import DeeplinkWidget
from take_home.causal_chains.agents.models.run_clients import RunClients
from take_home.causal_chains.agents.models.run_config import RunConfig
from take_home.causal_chains.agents.models.run_context import RunContext


def test_app_agent_runner_streams_one_run(monkeypatch):
    class FakeDelta:
        def __init__(
            self,
            delta: str,
        ) -> None:
            self.delta = delta

    async def fake_stream():
        yield SimpleNamespace(type="raw_response_event", data=FakeDelta("oil "))
        yield SimpleNamespace(type="raw_response_event", data=object())

    prompts: list[str] = []
    seen: list[object] = []
    contexts: list[object] = []
    cache = InMemoryMemcache()

    class FakeResult:
        final_output = "ok"
        cancelled = False

        def stream_events(self):
            return fake_stream()

        def cancel(self):
            self.cancelled = True

    class FakeRunner:
        @staticmethod
        def run_streamed(
            agent,
            input,
            context=None,
        ):
            seen.append(agent)
            contexts.append(context)
            prompts.append(input)
            cache.append("span\n")
            return FakeResult()

    monkeypatch.setattr(app_agent_runner_module, "ResponseTextDeltaEvent", FakeDelta)
    monkeypatch.setattr(app_agent_runner_module, "Runner", FakeRunner)

    context = RunContext(
        conversation_id="1",
        turn_id="t_1",
        run_config=RunConfig(include_traces=True, attempt_quota=2),
        clients=RunClients(causal_chain_store=object()),
    )

    async def collect():
        runner = AppAgentRunner(api_key="test", memcache=cache)
        return [event async for event in runner.stream(["hormuz"], context)]

    events = asyncio.run(collect())
    assert contexts == [context]
    assert seen == [causal_chain]
    assert prompts == ["Future situation:\nhormuz\nRemaining attempts: 2"]
    deltas = [event.text for event in events if event.type == "delta"]
    assert deltas == ["oil "]
    assert events[-2].type == "run_traces"
    assert events[-2].text == "span\n"
    assert cache.flush() == ""
    assert events[-1].type == "done"
    assert events[-1].message_id == "m_t_1"


def test_app_agent_runner_omits_run_traces_by_default(monkeypatch):
    class FakeDelta:
        def __init__(
            self,
            delta: str,
        ) -> None:
            self.delta = delta

    async def fake_stream():
        yield SimpleNamespace(type="raw_response_event", data=FakeDelta("oil "))

    cache = InMemoryMemcache()

    class FakeResult:
        final_output = "not a graph"

        def stream_events(self):
            return fake_stream()

        def cancel(self) -> None:
            return None

    class FakeRunner:
        @staticmethod
        def run_streamed(
            agent,
            input,
            context=None,
        ):
            cache.append("span\n")
            return FakeResult()

    monkeypatch.setattr(app_agent_runner_module, "ResponseTextDeltaEvent", FakeDelta)
    monkeypatch.setattr(app_agent_runner_module, "Runner", FakeRunner)

    async def collect():
        runner = AppAgentRunner(api_key="test", memcache=cache)
        context = RunContext(
            conversation_id="1",
            turn_id="t_1",
            clients=RunClients(causal_chain_store=object()),
        )
        return [event async for event in runner.stream(["hormuz"], context)]

    events = asyncio.run(collect())
    assert all(event.type != "run_traces" for event in events)
    assert cache.flush() == ""
    assert events[-1].type == "done"


def test_app_agent_runner_emits_heartbeat_while_the_model_is_slow(monkeypatch):
    class FakeDelta:
        def __init__(
            self,
            delta: str,
        ) -> None:
            self.delta = delta

    async def fake_stream():
        await anyio.sleep(0.05)
        yield SimpleNamespace(type="raw_response_event", data=FakeDelta("oil "))

    class FakeResult:
        def stream_events(self):
            return fake_stream()

        def cancel(self) -> None:
            return None

    class FakeRunner:
        @staticmethod
        def run_streamed(
            agent,
            input,
            context=None,
        ):
            return FakeResult()

    monkeypatch.setattr(app_agent_runner_module, "ResponseTextDeltaEvent", FakeDelta)
    monkeypatch.setattr(app_agent_runner_module, "Runner", FakeRunner)

    async def collect():
        runner = AppAgentRunner(api_key="test", memcache=InMemoryMemcache())
        context = RunContext(
            conversation_id="1",
            turn_id="t_1",
            clients=RunClients(causal_chain_store=object()),
        )
        return [
            event
            async for event in runner.stream(["hormuz"], context, interval_s=0.01)
        ]

    events = asyncio.run(collect())
    types = [event.type for event in events]
    assert "heartbeat" in types
    assert types.index("heartbeat") < types.index("done")
    assert types[-1] == "done"


def test_app_agent_runner_streams_a_deeplink_widget(monkeypatch):
    now_id = UUID("11111111-1111-4111-8111-111111111111")
    card = DeeplinkCard(title="now", root_situation_id=now_id, root_version=1)

    async def fake_stream():
        yield SimpleNamespace(
            type="run_item_stream_event",
            item=SimpleNamespace(
                type="tool_call_item",
                raw_item=SimpleNamespace(name="make_deeplink_widget", call_id="call_1"),
            ),
        )
        yield SimpleNamespace(
            type="run_item_stream_event",
            item=SimpleNamespace(
                type="tool_call_output_item",
                raw_item={"call_id": "call_1"},
                output=card,
            ),
        )
        yield SimpleNamespace(
            type="run_item_stream_event",
            item=SimpleNamespace(
                type="tool_call_item",
                raw_item=SimpleNamespace(name="add_situation", call_id="call_2"),
            ),
        )
        yield SimpleNamespace(
            type="run_item_stream_event",
            item=SimpleNamespace(
                type="tool_call_output_item",
                raw_item={"call_id": "call_2"},
                output="saved",
            ),
        )

    class FakeResult:
        def stream_events(self):
            return fake_stream()

        def cancel(self) -> None:
            return None

    class FakeRunner:
        @staticmethod
        def run_streamed(
            agent,
            input,
            context=None,
        ):
            return FakeResult()

    monkeypatch.setattr(app_agent_runner_module, "Runner", FakeRunner)

    async def collect():
        runner = AppAgentRunner(api_key="test", memcache=InMemoryMemcache())
        context = RunContext(
            conversation_id="1",
            turn_id="t_1",
            clients=RunClients(causal_chain_store=object()),
        )
        return [event async for event in runner.stream(["hormuz"], context)]

    events = asyncio.run(collect())
    widgets = [event for event in events if isinstance(event, DeeplinkWidget)]
    assert widgets == [DeeplinkWidget(card=card)]
    assert [event.name for event in events if event.type == "tool"] == [
        "make_deeplink_widget",
        "add_situation",
    ]
