import asyncio
import logging
from collections.abc import AsyncIterator
from datetime import datetime, timezone

import pytest

import take_home.causal_chains.agents.chat_service.chat_service as chat_service_module
from take_home.causal_chains.agents.chat_service.chat_service import (
    ChatService,
    can_store_message,
    format_sse,
    update_turn,
)
from take_home.causal_chains.agents.models.messaging.message import (
    HeartbeatMessage,
    MarkdownMessage,
    Message,
    Role,
)
from take_home.causal_chains.agents.models.messaging.message_widgets import (
    DeeplinkCardMessage,
)
from take_home.causal_chains.agents.models.turn.turn import Turn
from take_home.causal_chains.agents.models.turn.turn_status import TurnStatus
from take_home.causal_chains.agents.models.run_clients import RunClients
from take_home.causal_chains.agents.models.run_context import RunContext
from take_home.causal_chains.agents.stores.messaging_store.messaging_store import (
    MessagingStoreImpl,
)
from take_home.causal_chains.agents.stores.turn_store.in_mem_turn_store import InMemoryTurnStore
from take_home.causal_chains.agents.stub_runner.stub_turn_runner import StubTurnRunner


class _FixedClock:
    def now(self) -> datetime:
        return datetime(2026, 9, 29, 5, 16, tzinfo=timezone.utc)


class _CancellableStream:
    def __init__(self, source: AsyncIterator[Message]) -> None:
        self._source = source

    def cancel(self) -> None:
        return

    def __aiter__(self) -> AsyncIterator[Message]:
        return self._source

    async def aclose(self) -> None:
        aclose = getattr(self._source, "aclose", None)
        if aclose is not None:
            await aclose()


def test_stores_user_and_agent_messages_only():
    created = datetime(2026, 9, 30, tzinfo=timezone.utc)
    user = MarkdownMessage(
        message_id="m_user",
        conversation_id="1",
        user_uuid="user-1",
        role=Role.user,
        text="hello",
        created_timestamp=created,
    )
    agent = user.model_copy(update={"message_id": "m_agent", "role": Role.agent})
    other = DeeplinkCardMessage(
        message_id="m_card",
        conversation_id="1",
        user_uuid="user-1",
        role=Role.other,
        created_timestamp=created,
        title="now",
        subtitle="the present",
        link="/chain/now",
        enabled=True,
    )
    assert can_store_message(user) is True
    assert can_store_message(agent) is True
    assert can_store_message(other) is False
    assert can_store_message(HeartbeatMessage()) is False


def test_format_sse_excludes_type_from_data():
    line = format_sse(
        MarkdownMessage(
            message_id="m_1",
            conversation_id="1",
            user_uuid="user-1",
            role=Role.agent,
            text="oil ",
            created_timestamp=datetime(2026, 9, 30, tzinfo=timezone.utc),
        ),
    )
    assert line.startswith("event: markdown\n")
    assert '"type"' not in line.split("data:", 1)[1]
    assert "oil" in line


def test_format_sse_deeplink():
    line = format_sse(
        DeeplinkCardMessage(
            message_id="m_2",
            conversation_id="1",
            user_uuid="user-1",
            role=Role.other,
            created_timestamp=datetime(2026, 9, 30, tzinfo=timezone.utc),
            title="now",
            subtitle="the present",
            link="/chain/now",
            enabled=True,
        ),
    )
    assert line.startswith("event: deeplink\n")
    assert "/chain/now" in line
    assert '"enabled":true' in line or '"enabled": true' in line


def test_format_sse_heartbeat():
    line = format_sse(HeartbeatMessage())
    assert line.startswith("event: heartbeat\n")
    assert "meta" in line
    assert "message_id" not in line


class _ChainStore:
    pass


class _FakeDynamoDb:
    def __init__(self) -> None:
        self._items: dict[tuple[str, tuple[tuple[str, object], ...]], dict[str, object]] = {}

    def put_item(self, table_name: str, item: dict[str, object]) -> None:
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


def _user_turn(message_id: str = "m_user") -> tuple[MarkdownMessage, Turn]:
    message = MarkdownMessage(
        message_id=message_id,
        conversation_id="1",
        user_uuid="user-1",
        role=Role.user,
        text="hello",
        created_timestamp=datetime(2026, 9, 30, tzinfo=timezone.utc),
    )
    turn = Turn(
        turn_id="t_1",
        conversation_id="1",
        status=TurnStatus.queued,
        from_message=message.message_id,
    )
    return message, turn


def test_update_turn_completes_or_fails():
    async def succeed():
        store = InMemoryTurnStore()
        _message, turn = _user_turn()
        async with update_turn(store, turn) as turn_is_open:
            assert turn_is_open is True
            running = await store.get_turn(turn.turn_id)
        finished = await store.get_turn(turn.turn_id)
        return running, finished

    async def fail():
        store = InMemoryTurnStore()
        _message, turn = _user_turn("m_fail")
        turn = turn.model_copy(update={"turn_id": "t_fail"})
        try:
            async with update_turn(store, turn):
                raise RuntimeError("boom")
        except RuntimeError:
            return await store.get_turn(turn.turn_id)
        return turn

    running, finished = asyncio.run(succeed())
    failed = asyncio.run(fail())
    assert running is not None and running.status is TurnStatus.running
    assert finished is not None and finished.status is TurnStatus.completed
    assert failed is not None and failed.status is TurnStatus.failed


def test_update_turn_keeps_a_cancelled_turn():
    async def cancelled_while_running():
        store = InMemoryTurnStore()
        _message, turn = _user_turn()
        await store.put_turn(turn)
        async with update_turn(store, turn):
            current = await store.get_turn(turn.turn_id)
            assert current is not None
            await store.put_turn(
                current.model_copy(update={"status": TurnStatus.cancelled}),
            )
        return await store.get_turn(turn.turn_id)

    async def already_cancelled():
        store = InMemoryTurnStore()
        _message, turn = _user_turn("m_cancelled")
        turn = turn.model_copy(update={"turn_id": "t_cancelled"})
        cancelled = turn.model_copy(update={"status": TurnStatus.cancelled})
        await store.put_turn(cancelled)
        async with update_turn(store, turn) as turn_is_open:
            assert turn_is_open is False
            return await store.get_turn(turn.turn_id)

    finished = asyncio.run(cancelled_while_running())
    untouched = asyncio.run(already_cancelled())
    assert finished is not None and finished.status is TurnStatus.cancelled
    assert untouched is not None and untouched.status is TurnStatus.cancelled


def test_run_turn_yields_runner_messages_and_completes():
    async def exercise():
        store = MessagingStoreImpl(_FakeDynamoDb(), "user-1")
        turn_store = InMemoryTurnStore()
        service = ChatService(
            StubTurnRunner(),
            store,
            turn_store,
            _ChainStore(),
            _FixedClock(),
        )
        message, turn = _user_turn()
        await store.append("1", message)
        await turn_store.put_turn(turn)
        events = [event async for event in service.run_turn(turn, message.text)]
        stored = (await store.list_messages("1", 20)).messages
        saved = await turn_store.get_turn(turn.turn_id)
        return events, stored, saved

    events, stored, saved = asyncio.run(exercise())
    assert len(events) == 1
    assert isinstance(events[0], MarkdownMessage)
    assert events[0].role is Role.agent
    assert events[0].text == "echo: hello"
    assert [message.role for message in stored] == [Role.user, Role.agent]
    assert [message.text for message in stored] == ["hello", "echo: hello"]
    assert saved is not None
    assert saved.from_message == "m_user"
    assert saved.status is TurnStatus.completed


def test_run_turn_stops_when_the_turn_is_cancelled():
    class _StopBeforeSecond:
        def __init__(self, turn_store: InMemoryTurnStore, turn: Turn) -> None:
            self._turn_store = turn_store
            self._turn = turn

        async def stream(self, inputs: list[str], context: RunContext):
            return _CancellableStream(self._events(inputs, context))

        async def _events(self, inputs: list[str], context: RunContext):
            del inputs, context
            created = datetime(2026, 9, 30, 0, 1, tzinfo=timezone.utc)
            yield MarkdownMessage(
                message_id="m_one",
                conversation_id="1",
                user_uuid="user-1",
                role=Role.agent,
                text="one",
                created_timestamp=created,
            )
            await self._turn_store.put_turn(
                self._turn.model_copy(update={"status": TurnStatus.cancelled}),
            )
            yield MarkdownMessage(
                message_id="m_two",
                conversation_id="1",
                user_uuid="user-1",
                role=Role.agent,
                text="two",
                created_timestamp=created,
            )

    async def exercise():
        store = MessagingStoreImpl(_FakeDynamoDb(), "user-1")
        turn_store = InMemoryTurnStore()
        message, turn = _user_turn()
        service = ChatService(
            _StopBeforeSecond(turn_store, turn),
            store,
            turn_store,
            _ChainStore(),
            _FixedClock(),
        )
        await store.append("1", message)
        await turn_store.put_turn(turn)
        events = [event async for event in service.run_turn(turn, message.text)]
        stored = (await store.list_messages("1", 20)).messages
        saved = await turn_store.get_turn(turn.turn_id)
        return events, stored, saved

    events, stored, saved = asyncio.run(exercise())
    assert [event.text for event in events if isinstance(event, MarkdownMessage)] == ["one"]
    assert [message.text for message in stored] == ["hello", "one"]
    assert saved is not None and saved.status is TurnStatus.cancelled


def test_run_turn_logs_the_cancellation_error(caplog: pytest.LogCaptureFixture):
    class _CancelOnClose:
        def __init__(self, turn_store: InMemoryTurnStore, turn: Turn) -> None:
            self._turn_store = turn_store
            self._turn = turn

        async def stream(self, inputs: list[str], context: RunContext):
            return _CancellableStream(self._events(inputs, context))

        async def _events(self, inputs: list[str], context: RunContext):
            del inputs, context
            try:
                created = datetime(2026, 9, 30, 0, 1, tzinfo=timezone.utc)
                yield MarkdownMessage(
                    message_id="m_one",
                    conversation_id="1",
                    user_uuid="user-1",
                    role=Role.agent,
                    text="one",
                    created_timestamp=created,
                )
                await self._turn_store.put_turn(
                    self._turn.model_copy(update={"status": TurnStatus.cancelled}),
                )
                yield MarkdownMessage(
                    message_id="m_two",
                    conversation_id="1",
                    user_uuid="user-1",
                    role=Role.agent,
                    text="two",
                    created_timestamp=created,
                )
            finally:
                raise asyncio.CancelledError()

    async def exercise():
        store = MessagingStoreImpl(_FakeDynamoDb(), "user-1")
        turn_store = InMemoryTurnStore()
        message, turn = _user_turn()
        service = ChatService(
            _CancelOnClose(turn_store, turn),
            store,
            turn_store,
            _ChainStore(),
            _FixedClock(),
        )
        await store.append("1", message)
        await turn_store.put_turn(turn)
        events = [event async for event in service.run_turn(turn, message.text)]
        saved = await turn_store.get_turn(turn.turn_id)
        return events, saved

    with caplog.at_level(logging.ERROR, logger="agents"):
        events, saved = asyncio.run(exercise())
    assert [event.text for event in events if isinstance(event, MarkdownMessage)] == ["one"]
    assert saved is not None and saved.status is TurnStatus.cancelled
    assert "turn stream cancelled" in caplog.text


def test_run_turn_skips_heartbeats_and_other_roles():
    class _Mixed:
        async def stream(self, inputs: list[str], context: RunContext):
            return _CancellableStream(self._events(inputs, context))

        async def _events(self, inputs: list[str], context: RunContext):
            del inputs, context
            yield HeartbeatMessage()
            yield DeeplinkCardMessage(
                message_id="m_card",
                conversation_id="1",
                user_uuid="user-1",
                role=Role.other,
                created_timestamp=datetime(2026, 9, 30, 0, 1, tzinfo=timezone.utc),
                title="now",
                subtitle="the present",
                link="/chain/now",
                enabled=True,
            )
            yield MarkdownMessage(
                message_id="m_follow",
                conversation_id="1",
                user_uuid="user-1",
                role=Role.user,
                text="follow up",
                created_timestamp=datetime(2026, 9, 30, 0, 2, tzinfo=timezone.utc),
            )
            yield MarkdownMessage(
                message_id="m_answer",
                conversation_id="1",
                user_uuid="user-1",
                role=Role.agent,
                text="answer",
                created_timestamp=datetime(2026, 9, 30, 0, 3, tzinfo=timezone.utc),
            )

    async def exercise():
        store = MessagingStoreImpl(_FakeDynamoDb(), "user-1")
        service = ChatService(
            _Mixed(),
            store,
            InMemoryTurnStore(),
            _ChainStore(),
            _FixedClock(),
        )
        _message, turn = _user_turn()
        events = [event async for event in service.run_turn(turn, "hello")]
        stored = (await store.list_messages("1", 20)).messages
        return events, stored

    events, stored = asyncio.run(exercise())
    assert [event.kind for event in events] == [
        "heartbeat",
        "deeplink",
        "markdown",
        "markdown",
    ]
    assert [(message.message_id, message.text) for message in stored] == [
        ("m_follow", "follow up"),
        ("m_answer", "answer"),
    ]


def test_run_turn_builds_run_clients():
    chain_store = _ChainStore()
    clock = _FixedClock()

    class _Recording:
        def __init__(self) -> None:
            self.contexts: list[RunContext] = []

        async def stream(self, inputs: list[str], context: RunContext):
            return _CancellableStream(self._events(inputs, context))

        async def _events(self, inputs: list[str], context: RunContext):
            self.contexts.append(context)
            if False:
                yield MarkdownMessage(
                    message_id="m_1",
                    conversation_id="1",
                    user_uuid="user-1",
                    role=Role.agent,
                    text="",
                    created_timestamp=datetime(2026, 9, 30, tzinfo=timezone.utc),
                )

    async def exercise():
        runner = _Recording()
        service = ChatService(
            runner,
            MessagingStoreImpl(_FakeDynamoDb(), "user-1"),
            InMemoryTurnStore(),
            chain_store,
            clock,
        )
        _message, turn = _user_turn()
        async for _event in service.run_turn(turn, "hello"):
            pass
        return runner.contexts

    contexts = asyncio.run(exercise())
    assert len(contexts) == 1
    clients = contexts[0].clients
    assert isinstance(clients, RunClients)
    assert clients.causal_chain_store is chain_store
    assert contexts[0].clock is clock


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
            MessagingStoreImpl(_FakeDynamoDb(), "user-1"),
            InMemoryTurnStore(),
            _ChainStore(),
            _FixedClock(),
        )
        _message, turn = _user_turn()
        async for _event in service.run_turn(turn, "hello"):
            pass
        return turn

    turn = asyncio.run(exercise())
    assert opened == [
        ("chat_service", "1", {"turn_id": turn.turn_id}),
    ]
    assert flushed_while_open == [False]
