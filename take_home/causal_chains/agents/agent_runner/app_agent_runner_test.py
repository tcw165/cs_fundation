import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import UUID

import anyio
from agents.run_config import CallModelData, ModelInputData

import take_home.causal_chains.agents.agent_runner.app_agent_runner as app_agent_runner_module
from take_home.causal_chains.agents.agent_runner.app_agent_runner import (
    AppAgentRunner,
    _decorate_tail_messages,
)
from take_home.causal_chains.agents.agents.causal_chain.causal_chain import (
    causal_chain,
)
from take_home.causal_chains.agents.clients.memcache.memcache import InMemoryMemcache
from take_home.causal_chains.agents.models.messaging.deeplink_card import DeeplinkCard
from take_home.causal_chains.agents.models.messaging.message import (
    DeeplinkCardMessage,
    HeartbeatMessage,
    MarkdownMessage,
    Role,
)
from take_home.causal_chains.agents.models.run_clients import RunClients
from take_home.causal_chains.agents.models.run_config import RunConfig
from take_home.causal_chains.agents.models.run_context import RunContext


class _FixedClock:
    def now(self) -> datetime:
        return datetime(2026, 9, 29, 5, 16, tzinfo=timezone.utc)


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
    seen_max_turns: list[int | None] = []
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
            max_turns=None,
            run_config=None,
        ):
            seen.append(agent)
            contexts.append(context)
            prompts.append(input)
            seen_max_turns.append(max_turns)
            cache.append("span\n")
            return FakeResult()

    monkeypatch.setattr(app_agent_runner_module, "ResponseTextDeltaEvent", FakeDelta)
    monkeypatch.setattr(app_agent_runner_module, "Runner", FakeRunner)

    context = RunContext(
        conversation_id="1",
        clock=_FixedClock(),
        turn_id="t_1",
        run_config=RunConfig(include_traces=True, causal_chain_max_steps=2),
        clients=RunClients(causal_chain_store=object()),
    )

    async def collect():
        runner = AppAgentRunner(api_key="test", memcache=cache)
        return [event async for event in runner.stream(["hormuz"], context)]

    events = asyncio.run(collect())
    assert contexts == [context]
    assert seen == [causal_chain]
    assert prompts == ["hormuz"]
    assert seen_max_turns == [2]
    assert [type(event) for event in events] == [MarkdownMessage]
    assert events[0].role is Role.agent
    assert events[0].text == "oil "
    assert cache.flush() == ""


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
            max_turns=None,
            run_config=None,
        ):
            cache.append("span\n")
            return FakeResult()

    monkeypatch.setattr(app_agent_runner_module, "ResponseTextDeltaEvent", FakeDelta)
    monkeypatch.setattr(app_agent_runner_module, "Runner", FakeRunner)

    async def collect():
        runner = AppAgentRunner(api_key="test", memcache=cache)
        context = RunContext(
            conversation_id="1",
            clock=_FixedClock(),
            turn_id="t_1",
            clients=RunClients(causal_chain_store=object()),
        )
        return [event async for event in runner.stream(["hormuz"], context)]

    events = asyncio.run(collect())
    assert [event.text for event in events] == ["oil "]
    assert all(isinstance(event, MarkdownMessage) for event in events)
    assert cache.flush() == ""


def test_app_agent_runner_cuts_markdown_on_a_blank_line(monkeypatch):
    class FakeDelta:
        def __init__(
            self,
            delta: str,
        ) -> None:
            self.delta = delta

    async def fake_stream():
        yield SimpleNamespace(
            type="raw_response_event",
            data=FakeDelta("one\n\ntwo\n\nthree"),
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
            max_turns=None,
            run_config=None,
        ):
            return FakeResult()

    monkeypatch.setattr(app_agent_runner_module, "ResponseTextDeltaEvent", FakeDelta)
    monkeypatch.setattr(app_agent_runner_module, "Runner", FakeRunner)

    async def collect():
        runner = AppAgentRunner(api_key="test", memcache=InMemoryMemcache())
        context = RunContext(
            conversation_id="1",
            clock=_FixedClock(),
            turn_id="t_1",
            clients=RunClients(causal_chain_store=object()),
        )
        return [event async for event in runner.stream(["hormuz"], context)]

    events = asyncio.run(collect())
    assert [event.text for event in events] == ["one", "two", "three"]
    assert all(isinstance(event, MarkdownMessage) for event in events)
    assert all(event.role is Role.agent for event in events)
    assert len({event.message_id for event in events}) == 3


def test_app_agent_runner_flushes_a_preamble_when_a_tool_call_starts(monkeypatch):
    class FakeDelta:
        def __init__(
            self,
            delta: str,
        ) -> None:
            self.delta = delta

    def _tool_call(name: str, call_id: str) -> SimpleNamespace:
        return SimpleNamespace(
            type="run_item_stream_event",
            item=SimpleNamespace(
                type="tool_call_item",
                raw_item=SimpleNamespace(name=name, call_id=call_id),
            ),
        )

    async def fake_stream():
        yield SimpleNamespace(
            type="raw_response_event",
            data=FakeDelta("preamble one"),
        )
        yield _tool_call("add_case", "call_1")
        yield SimpleNamespace(
            type="raw_response_event",
            data=FakeDelta("preamble two"),
        )
        yield _tool_call("lookup_chain_so_far", "call_2")
        yield SimpleNamespace(
            type="raw_response_event",
            data=FakeDelta("the story"),
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
            max_turns=None,
            run_config=None,
        ):
            return FakeResult()

    monkeypatch.setattr(app_agent_runner_module, "ResponseTextDeltaEvent", FakeDelta)
    monkeypatch.setattr(app_agent_runner_module, "Runner", FakeRunner)

    async def collect():
        runner = AppAgentRunner(api_key="test", memcache=InMemoryMemcache())
        context = RunContext(
            conversation_id="1",
            clock=_FixedClock(),
            turn_id="t_1",
            clients=RunClients(causal_chain_store=object()),
        )
        return [event async for event in runner.stream(["hormuz"], context)]

    events = asyncio.run(collect())
    assert [event.text for event in events] == [
        "preamble one",
        "preamble two",
        "the story",
    ]
    assert all(isinstance(event, MarkdownMessage) for event in events)
    assert len({event.message_id for event in events}) == 3


def test_app_agent_runner_emits_a_heartbeat_while_the_model_is_slow(monkeypatch):
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
            max_turns=None,
            run_config=None,
        ):
            return FakeResult()

    monkeypatch.setattr(app_agent_runner_module, "ResponseTextDeltaEvent", FakeDelta)
    monkeypatch.setattr(app_agent_runner_module, "Runner", FakeRunner)

    async def collect():
        runner = AppAgentRunner(api_key="test", memcache=InMemoryMemcache())
        context = RunContext(
            conversation_id="1",
            clock=_FixedClock(),
            turn_id="t_1",
            clients=RunClients(causal_chain_store=object()),
        )
        return [
            event
            async for event in runner.stream(["hormuz"], context, interval_s=0.01)
        ]

    events = asyncio.run(collect())
    beats = [event for event in events if isinstance(event, HeartbeatMessage)]
    assert beats
    assert all(event.role is Role.meta for event in beats)
    assert all(event.type == "heartbeat" for event in beats)
    markdown = [event for event in events if isinstance(event, MarkdownMessage)]
    assert [event.text for event in markdown] == ["oil "]
    assert events.index(beats[0]) < events.index(markdown[0])


def test_app_agent_runner_streams_a_deeplink_widget(monkeypatch):
    now_id = UUID("11111111-1111-4111-8111-111111111111")
    card = DeeplinkCard(title="now", root_situation_id=now_id, root_version=1)

    class FakeDelta:
        def __init__(
            self,
            delta: str,
        ) -> None:
            self.delta = delta

    async def fake_stream():
        yield SimpleNamespace(
            type="raw_response_event",
            data=FakeDelta("saved the chain"),
        )
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
            max_turns=None,
            run_config=None,
        ):
            return FakeResult()

    monkeypatch.setattr(app_agent_runner_module, "ResponseTextDeltaEvent", FakeDelta)
    monkeypatch.setattr(app_agent_runner_module, "Runner", FakeRunner)

    async def collect():
        runner = AppAgentRunner(api_key="test", memcache=InMemoryMemcache())
        context = RunContext(
            conversation_id="1",
            clock=_FixedClock(),
            turn_id="t_1",
            clients=RunClients(causal_chain_store=object()),
        )
        return [event async for event in runner.stream(["hormuz"], context)]

    events = asyncio.run(collect())
    assert isinstance(events[0], MarkdownMessage)
    assert events[0].text == "saved the chain"
    message = events[1]
    assert isinstance(message, DeeplinkCardMessage)
    assert message.role is Role.other
    assert message.link == f"/chain/{now_id}/1?title=now"
    assert len(events) == 2


def test_app_agent_runner_traces_the_model_run(monkeypatch):
    opened: list[tuple[str, str | None, dict[str, str] | None]] = []
    active = {"value": False}
    ran_inside: list[bool] = []

    class _Trace:
        def __init__(
            self,
            name: str,
            group_id: str | None = None,
            metadata: dict[str, str] | None = None,
        ) -> None:
            self._name = name
            self._group_id = group_id
            self._metadata = metadata

        def __enter__(self) -> "_Trace":
            active["value"] = True
            opened.append((self._name, self._group_id, self._metadata))
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            active["value"] = False

    class FakeResult:
        def stream_events(self):
            async def empty():
                if False:
                    yield None

            return empty()

        def cancel(self) -> None:
            return None

    class FakeRunner:
        @staticmethod
        def run_streamed(
            agent,
            input,
            context=None,
            max_turns=None,
            run_config=None,
        ):
            ran_inside.append(active["value"])
            return FakeResult()

    monkeypatch.setattr(app_agent_runner_module, "trace", _Trace)
    monkeypatch.setattr(app_agent_runner_module, "Runner", FakeRunner)

    async def collect():
        runner = AppAgentRunner(api_key="test", memcache=InMemoryMemcache())
        context = RunContext(
            conversation_id="1",
            clock=_FixedClock(),
            turn_id="t_1",
            clients=RunClients(causal_chain_store=object()),
        )
        return [event async for event in runner.stream(["hormuz"], context)]

    events = asyncio.run(collect())
    assert ran_inside == [True]
    assert opened == [("app_agent_runner", "1", {"turn_id": "t_1"})]
    assert events == []


def test_decorate_tail_messages_refreshes_the_clock_before_the_user():
    context = RunContext(
        conversation_id="1",
        clock=_FixedClock(),
        turn_id="t_1",
        clients=RunClients(causal_chain_store=object()),
    )
    data = CallModelData(
        model_data=ModelInputData(
            input=[
                {
                    "role": "assistant",
                    "content": "Current time: 2020-01-01T00:00:00+00:00 UTC",
                },
                {"role": "user", "content": "Future situation:\nopen"},
            ],
            instructions="stay",
        ),
        agent=causal_chain,
        context=context,
    )
    updated = _decorate_tail_messages(data)
    assert updated.instructions == "stay"
    assert updated.input[0] == {
        "role": "assistant",
        "content": "Current time: 2026-09-29T05:16:00+00:00 UTC",
    }
    assert updated.input[1]["role"] == "user"
