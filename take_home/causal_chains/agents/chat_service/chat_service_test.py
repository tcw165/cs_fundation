import asyncio

import take_home.causal_chains.agents.chat_service.chat_service as chat_service_module
from take_home.causal_chains.agents.chat_service.chat_service import ChatService, format_sse
from take_home.causal_chains.agents.models.run_clients import RunClients
from take_home.causal_chains.agents.stores.messaging_store.messaging_store import (
    MessagingStoreImpl,
)
from take_home.causal_chains.agents.stores.turn_store.turn_store import InMemoryTurnStore
from take_home.causal_chains.agents.stub_runner.stub_turn_runner import StubTurnRunner
from take_home.causal_chains.agents.models.messaging.message import Role
from take_home.causal_chains.agents.models.messaging.sse_event import (
    RunTraces,
    SseDelta,
    SseHeartbeat,
)
from take_home.causal_chains.agents.models.messaging.turn_status import TurnStatus


def test_format_sse_excludes_type_from_data():
    line = format_sse(SseDelta(text="oil "))
    assert line.startswith("event: delta\n")
    assert '"type"' not in line.split("data:", 1)[1]
    assert "oil" in line


def test_format_sse_run_traces():
    line = format_sse(RunTraces(text="span\n"))
    assert line.startswith("event: run_traces\n")
    assert "span" in line


def test_format_sse_heartbeat():
    line = format_sse(SseHeartbeat())
    assert line.startswith("event: heartbeat\n")


class _ChainStore:
    pass


class _FakeDynamoDb:
    def __init__(self) -> None:
        self._items: dict[tuple[str, tuple[tuple[str, object], ...]], dict[str, object]] = {}
        self.put_item("conversation", {"conversation_id": "1", "messages": []})

    def put_item(self, table_name: str, item: dict[str, object]) -> None:
        key = (("conversation_id", item["conversation_id"]),)
        self._items[(table_name, key)] = item

    def get_item(self, table_name: str, key: dict[str, object]) -> dict[str, object] | None:
        stored_key = tuple(sorted(key.items()))
        return self._items.get((table_name, stored_key))


def test_post_message_and_subscribe_stub():
    async def exercise():
        store = MessagingStoreImpl(_FakeDynamoDb())
        turn_store = InMemoryTurnStore()
        service = ChatService(StubTurnRunner(), store, turn_store, _ChainStore())
        turn = await service.post_message("1", "hello")
        assert turn.status is TurnStatus.queued
        await service.run_turn(turn, "hello")
        events = [event async for event in service.subscribe("1", turn.turn_id)]
        stored = await store.list_messages("1")
        saved = await turn_store.get_turn(turn.turn_id)
        return turn, events, stored, saved

    turn, events, stored, saved = asyncio.run(exercise())
    assert events[0].type == "markdown"
    assert events[-1].type == "done"
    assert turn.conversation_id == "1"
    assert len(stored) == 1
    assert stored[0].role is Role.user
    assert stored[0].text == "hello"
    assert turn.from_message == stored[0].message_id
    assert saved is not None
    assert saved.status is TurnStatus.completed


def test_post_message_builds_run_clients():
    chain_store = _ChainStore()

    async def exercise():
        service = ChatService(
            StubTurnRunner(),
            MessagingStoreImpl(_FakeDynamoDb()),
            InMemoryTurnStore(),
            chain_store,
        )
        turn = await service.post_message("1", "hello")
        return service._contexts[turn.turn_id].clients

    clients = asyncio.run(exercise())
    assert isinstance(clients, RunClients)
    assert clients.causal_chain_store is chain_store


def test_run_turn_traces_chat_service_then_flushes(monkeypatch):
    opened: list[tuple[str, str | None, dict[str, str] | None]] = []
    flushed_while_open: list[bool] = []
    active = {"value": False}

    class _Trace:
        def __init__(
            self,
            workflow_name: str,
            group_id: str | None = None,
            metadata: dict[str, str] | None = None,
        ) -> None:
            self._name = workflow_name
            self._group_id = group_id
            self._metadata = metadata

        def __enter__(self) -> "_Trace":
            active["value"] = True
            opened.append((self._name, self._group_id, self._metadata))
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            active["value"] = False

    monkeypatch.setattr(chat_service_module, "trace", _Trace)
    monkeypatch.setattr(
        chat_service_module,
        "flush_traces",
        lambda: flushed_while_open.append(active["value"]),
    )

    async def exercise():
        service = ChatService(
            StubTurnRunner(),
            MessagingStoreImpl(_FakeDynamoDb()),
            InMemoryTurnStore(),
            _ChainStore(),
        )
        turn = await service.post_message("1", "hello")
        await service.run_turn(turn, "hello")
        return turn

    turn = asyncio.run(exercise())
    assert opened == [
        ("chat_service", "1", {"turn_id": turn.turn_id}),
    ]
    assert flushed_while_open == [False]
