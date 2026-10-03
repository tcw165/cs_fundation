import asyncio
import logging
from collections.abc import AsyncIterator
from datetime import datetime, timezone

import anyio
import pytest
from fastapi import BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse

from take_home.causal_chains.agents.chat_service.chat_service import ChatService
from take_home.causal_chains.agents.endpoints.conversation import (
    format_conversation_sse,
    get_messages,
    post_message,
    stop_turn,
    turn_sse,
)
from take_home.causal_chains.agents.http_models.post_message_body import PostMessageBody
from take_home.causal_chains.agents.endpoints.models.conversation_messages_response import (
    ConversationMessagesResponse,
)
from take_home.causal_chains.agents.endpoints.models.text_input_state import TextInputState
from take_home.causal_chains.agents.models.messaging.message import (
    MarkdownMessage,
    Message,
    Role,
)
from take_home.causal_chains.agents.models.turn.turn import Turn
from take_home.causal_chains.agents.models.turn.turn_status import TurnStatus
from take_home.causal_chains.agents.models.run_context import RunContext
from take_home.causal_chains.agents.stores.messaging_store.messaging_store import (
    MessagingStoreImpl,
)
from take_home.causal_chains.agents.stores.turn_store.in_mem_turn_store import InMemoryTurnStore


class _ChainStore:
    pass


class _FixedClock:
    def now(self) -> datetime:
        return datetime(2026, 9, 29, 5, 16, tzinfo=timezone.utc)


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


class _Scripted:
    def __init__(self) -> None:
        self.calls = 0
        self.contexts: list[RunContext] = []

    async def stream(self, inputs: list[Message], context: RunContext):
        return _CancellableStream(self._events(inputs, context))

    async def _events(self, inputs: list[Message], context: RunContext):
        del inputs
        self.calls += 1
        self.contexts.append(context)
        created = datetime(2026, 9, 30, tzinfo=timezone.utc)
        yield MarkdownMessage(
            message_id="m_a",
            conversation_id="1",
            user_uuid="user-1",
            role=Role.agent,
            text="one",
            created_timestamp=created,
        )
        yield MarkdownMessage(
            message_id="m_b",
            conversation_id="1",
            user_uuid="user-1",
            role=Role.agent,
            text="two",
            created_timestamp=created,
        )


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


class _Container:
    def __init__(
        self,
        service: ChatService,
        store: MessagingStoreImpl,
        turn_store: InMemoryTurnStore,
    ) -> None:
        self._service = service
        self._store = store
        self._turn_store = turn_store

    def chat_service(self) -> ChatService:
        return self._service

    def messaging_store(self) -> MessagingStoreImpl:
        return self._store

    def turn_store(self) -> InMemoryTurnStore:
        return self._turn_store


def _services() -> tuple[_Container, _Scripted, MessagingStoreImpl, InMemoryTurnStore]:
    store = MessagingStoreImpl(_FakeDynamoDb(), "user-1")
    turn_store = InMemoryTurnStore()
    runner = _Scripted()
    service = ChatService(runner, store, turn_store, _ChainStore(), _FixedClock())
    return _Container(service, store, turn_store), runner, store, turn_store


async def _drain_sse(response: StreamingResponse) -> str:
    chunks: list[str] = []
    async for chunk in response.body_iterator:
        chunks.append(chunk if isinstance(chunk, str) else chunk.decode())
    return "".join(chunks)


async def _read_sse(
    container: _Container,
    turn_id: str,
    after_message: str | None,
    after_message_timestamp: datetime | None,
) -> str:
    response = await turn_sse(
        "1",
        turn_id,
        container,
        after_message=after_message,
        after_message_timestamp=after_message_timestamp,
    )
    return await _drain_sse(response)


def test_post_message_stores_the_anchored_turn():
    async def exercise():
        container, _runner, store, turn_store = _services()
        posted = await post_message("1", PostMessageBody(text="hello"), container, BackgroundTasks())
        stored = (await store.list_messages("1", 20)).messages
        saved = await turn_store.get_turn(posted.turn.turn_id)
        return posted, stored, saved

    posted, stored, saved = asyncio.run(exercise())
    turn = posted.turn
    assert turn.status is TurnStatus.queued
    assert isinstance(posted.received_message, MarkdownMessage)
    assert posted.received_message.text == "hello"
    assert len(stored) == 1
    assert isinstance(stored[0], MarkdownMessage)
    assert stored[0].role is Role.user
    assert stored[0].text == "hello"
    assert turn.from_message == stored[0].message_id
    assert posted.received_message.message_id == stored[0].message_id
    assert saved is not None
    assert saved.from_message == stored[0].message_id
    assert saved.status is TurnStatus.queued


def test_post_message_logs_each_streamed_kind(caplog: pytest.LogCaptureFixture):
    async def exercise():
        container, _runner, _store, _turn_store = _services()
        tasks = BackgroundTasks()
        with caplog.at_level(logging.INFO, logger="agents"):
            await post_message(
                "1",
                PostMessageBody(text="hello"),
                container,
                tasks,
            )
            await tasks()

    asyncio.run(exercise())
    assert "received user message" in caplog.text
    assert "queued turn" in caplog.text
    assert caplog.text.count("streamed message kind=markdown") == 2


def test_post_message_accepts_another_turn_after_the_first_finishes():
    async def exercise():
        container, _runner, _store, turn_store = _services()
        tasks = BackgroundTasks()
        first = await post_message("1", PostMessageBody(text="first"), container, tasks)
        await tasks()
        second = await post_message(
            "1",
            PostMessageBody(text="second"),
            container,
            BackgroundTasks(),
        )
        saved = await turn_store.get_turn(first.turn.turn_id)
        return saved, second

    saved, second = asyncio.run(exercise())
    assert saved is not None and saved.status is TurnStatus.completed
    assert second.received_message.text == "second"


@pytest.mark.parametrize(
    "status",
    [TurnStatus.completed, TurnStatus.failed, TurnStatus.cancelled, TurnStatus.timeout],
)
def test_post_message_accepts_a_turn_when_the_stored_one_has_ended(status: TurnStatus):
    async def exercise():
        container, _runner, _store, turn_store = _services()
        await turn_store.put_turn(
            Turn(
                turn_id="t_old",
                conversation_id="1",
                status=status,
                from_message="m_old",
            ),
        )
        return await post_message(
            "1",
            PostMessageBody(text="next"),
            container,
            BackgroundTasks(),
        )

    posted = asyncio.run(exercise())
    assert posted.received_message.text == "next"


def test_post_message_rejects_a_running_turn_beside_a_finished_one():
    async def exercise():
        container, _runner, _store, turn_store = _services()
        tasks = BackgroundTasks()
        first = await post_message("1", PostMessageBody(text="first"), container, tasks)
        await tasks()
        await turn_store.put_turn(
            Turn(
                turn_id="t_open",
                conversation_id="1",
                status=TurnStatus.running,
                from_message=first.turn.from_message,
            ),
        )
        await post_message("1", PostMessageBody(text="second"), container, BackgroundTasks())

    with pytest.raises(HTTPException) as raised:
        asyncio.run(exercise())
    assert raised.value.status_code == 409
    assert raised.value.detail == "conversation already has a turn"


def test_stop_turn_marks_an_open_turn_cancelled():
    async def exercise():
        container, _runner, _store, turn_store = _services()
        posted = await post_message(
            "1",
            PostMessageBody(text="hello"),
            container,
            BackgroundTasks(),
        )
        stopped = await stop_turn("1", posted.turn.turn_id, container)
        saved = await turn_store.get_turn(posted.turn.turn_id)
        return stopped, saved

    stopped, saved = asyncio.run(exercise())
    assert stopped.status is TurnStatus.cancelled
    assert saved == stopped


def test_stop_turn_leaves_a_finished_turn():
    async def exercise():
        container, _runner, _store, turn_store = _services()
        posted = await post_message(
            "1",
            PostMessageBody(text="hello"),
            container,
            BackgroundTasks(),
        )
        completed = posted.turn.model_copy(update={"status": TurnStatus.completed})
        await turn_store.put_turn(completed)
        stopped = await stop_turn("1", posted.turn.turn_id, container)
        return stopped, completed

    stopped, completed = asyncio.run(exercise())
    assert stopped == completed


def test_stop_turn_rejects_an_unknown_turn():
    async def exercise():
        container, _runner, _store, _turn_store = _services()
        await stop_turn("1", "t_missing", container)

    with pytest.raises(HTTPException) as raised:
        asyncio.run(exercise())
    assert raised.value.status_code == 404
    assert raised.value.detail == "turn not found"


def test_stop_turn_allows_another_message():
    async def exercise():
        container, _runner, _store, _turn_store = _services()
        posted = await post_message(
            "1",
            PostMessageBody(text="first"),
            container,
            BackgroundTasks(),
        )
        await stop_turn("1", posted.turn.turn_id, container)
        return await post_message(
            "1",
            PostMessageBody(text="second"),
            container,
            BackgroundTasks(),
        )

    second = asyncio.run(exercise())
    assert second.received_message.text == "second"


def test_post_message_rejects_a_second_turn():
    async def exercise():
        container, _runner, _store, _turn_store = _services()
        await post_message("1", PostMessageBody(text="first"), container, BackgroundTasks())
        await post_message("1", PostMessageBody(text="second"), container, BackgroundTasks())

    with pytest.raises(HTTPException) as raised:
        asyncio.run(exercise())
    assert raised.value.status_code == 409
    assert raised.value.detail == "conversation already has a turn"


def test_turn_sse_rejects_a_turn_from_another_conversation():
    async def exercise():
        container, _runner, _store, _turn_store = _services()
        posted = await post_message(
            "1",
            PostMessageBody(text="hello"),
            container,
            BackgroundTasks(),
        )
        await turn_sse(
            "2",
            posted.turn.turn_id,
            container,
            after_message=posted.turn.from_message,
            after_message_timestamp=posted.received_message.created_timestamp,
        )

    with pytest.raises(HTTPException) as raised:
        asyncio.run(exercise())
    assert raised.value.status_code == 404
    assert raised.value.detail == "turn not found"


def test_turn_sse_starts_at_the_oldest_message_without_a_cursor():
    async def exercise():
        container, _runner, _store, turn_store = _services()
        posted = await post_message(
            "1",
            PostMessageBody(text="hello"),
            container,
            BackgroundTasks(),
        )
        response = await turn_sse("1", posted.turn.turn_id, container)
        await turn_store.put_turn(
            posted.turn.model_copy(update={"status": TurnStatus.completed}),
        )
        return await _drain_sse(response)

    snapshots = _snapshots(asyncio.run(exercise()))
    assert snapshots[0].messages == []
    assert [snapshot.messages[0].text for snapshot in snapshots[1:-1]] == ["hello"]
    assert snapshots[-1].messages == []


def test_turn_sse_rejects_a_cursor_without_its_timestamp():
    async def exercise():
        container, _runner, _store, _turn_store = _services()
        posted = await post_message(
            "1",
            PostMessageBody(text="hello"),
            container,
            BackgroundTasks(),
        )
        await turn_sse(
            "1",
            posted.turn.turn_id,
            container,
            after_message=posted.turn.from_message,
        )

    with pytest.raises(HTTPException) as raised:
        asyncio.run(exercise())
    assert raised.value.status_code == 422
    assert raised.value.detail == "after_message and after_message_timestamp are a pair"


def test_get_messages_rejects_a_cursor_without_its_timestamp():
    async def exercise():
        container, _runner, _store, _turn_store = _services()
        await get_messages("1", container, limit=1, after_message="m_0")

    with pytest.raises(HTTPException) as raised:
        asyncio.run(exercise())
    assert raised.value.status_code == 422
    assert raised.value.detail == "after_message and after_message_timestamp are a pair"


def test_get_messages_returns_one_page():
    async def exercise():
        container, _runner, _store, _turn_store = _services()
        await post_message("1", PostMessageBody(text="first"), container, BackgroundTasks())
        await container.messaging_store().append(
            "1",
            MarkdownMessage(
                message_id="m_second",
                conversation_id="1",
                user_uuid="user-1",
                role=Role.user,
                text="second",
                created_timestamp=datetime(2099, 1, 1, tzinfo=timezone.utc),
            ),
        )
        page = await get_messages("1", container, limit=1)
        assert page.next_cursor is not None
        rest = await get_messages(
            "1",
            container,
            limit=1,
            after_message=page.next_cursor,
            after_message_timestamp=page.messages[-1].created_timestamp,
        )
        assert rest.next_cursor is not None
        done = await get_messages(
            "1",
            container,
            limit=1,
            after_message=rest.next_cursor,
            after_message_timestamp=rest.messages[-1].created_timestamp,
        )
        whole = await get_messages("1", container, limit=2)
        assert whole.next_cursor is not None
        after_whole = await get_messages(
            "1",
            container,
            limit=2,
            after_message=whole.next_cursor,
            after_message_timestamp=whole.messages[-1].created_timestamp,
        )
        return page, rest, done, whole, after_whole

    page, rest, done, whole, after_whole = asyncio.run(exercise())
    assert [message.text for message in page.messages] == ["first"]
    assert [message.text for message in rest.messages] == ["second"]
    assert done.messages == []
    assert done.next_cursor is None
    assert [message.text for message in whole.messages] == ["first", "second"]
    assert after_whole.messages == []
    assert after_whole.next_cursor is None


def _snapshots(body: str) -> list[ConversationMessagesResponse]:
    payloads: list[ConversationMessagesResponse] = []
    for block in body.split("\n\n"):
        if not block.strip():
            continue
        lines = block.split("\n")
        assert lines[0] == "event: conversation_messages"
        payload = lines[1].removeprefix("data: ")
        payloads.append(ConversationMessagesResponse.model_validate_json(payload))
    return payloads


def test_sse_streams_one_snapshot_per_emission():
    async def exercise():
        container, runner, store, turn_store = _services()
        posted = await post_message(
            "1",
            PostMessageBody(text="hello"),
            container,
            BackgroundTasks(),
        )
        await store.append(
            "1",
            MarkdownMessage(
                message_id="m_one",
                conversation_id="1",
                user_uuid="user-1",
                role=Role.agent,
                text="one",
                created_timestamp=datetime(2099, 1, 1, tzinfo=timezone.utc),
            ),
        )
        await store.append(
            "1",
            MarkdownMessage(
                message_id="m_two",
                conversation_id="1",
                user_uuid="user-1",
                role=Role.agent,
                text="two",
                created_timestamp=datetime(2099, 1, 2, tzinfo=timezone.utc),
            ),
        )
        response = await turn_sse(
            "1",
            posted.turn.turn_id,
            container,
            after_message=posted.turn.from_message,
            after_message_timestamp=posted.received_message.created_timestamp,
        )
        await turn_store.put_turn(
            posted.turn.model_copy(update={"status": TurnStatus.completed}),
        )
        everything = await _drain_sse(response)
        return everything, runner

    everything, runner = asyncio.run(exercise())
    snapshots = _snapshots(everything)
    assert snapshots[0].messages == []
    assert [snapshot.messages[0].text for snapshot in snapshots[1:-1]] == ["one", "two"]
    assert snapshots[-1].messages == []
    assert all(snapshot.conversation_id == "1" for snapshot in snapshots)
    assert all(len(snapshot.messages) == 1 for snapshot in snapshots[1:-1])
    assert snapshots[0].user_interaction_state.text_input_state is TextInputState.SEND_DISABLED
    assert snapshots[0].user_interaction_state.thinking_state is not None
    assert snapshots[0].user_interaction_state.thinking_state.text == "Thinking"
    assert snapshots[-1].user_interaction_state.text_input_state is TextInputState.ENABLED
    assert snapshots[-1].user_interaction_state.thinking_state is None
    assert snapshots[0].turn is not None
    assert len(snapshots[0].turn.processing) == 1
    assert snapshots[0].turn.queued == []
    assert runner.calls == 0


def test_turn_sse_rejects_an_ended_turn():
    async def exercise():
        container, _runner, _store, turn_store = _services()
        posted = await post_message(
            "1",
            PostMessageBody(text="hello"),
            container,
            BackgroundTasks(),
        )
        await turn_store.put_turn(
            posted.turn.model_copy(update={"status": TurnStatus.completed}),
        )
        await turn_sse("1", posted.turn.turn_id, container)

    with pytest.raises(HTTPException) as raised:
        asyncio.run(exercise())
    assert raised.value.status_code == 404
    assert raised.value.detail == "turn already ended"


def test_turn_sse_emits_thinking_before_the_first_message():
    async def exercise():
        container, _runner, _store, turn_store = _services()
        posted = await post_message(
            "1",
            PostMessageBody(text="hello"),
            container,
            BackgroundTasks(),
        )
        response = await turn_sse(
            "1",
            posted.turn.turn_id,
            container,
            after_message=posted.turn.from_message,
            after_message_timestamp=posted.received_message.created_timestamp,
        )
        first = await anext(response.body_iterator)
        chunk = first if isinstance(first, str) else first.decode()
        await turn_store.put_turn(
            posted.turn.model_copy(update={"status": TurnStatus.completed}),
        )
        async for rest in response.body_iterator:
            chunk += rest if isinstance(rest, str) else rest.decode()
        return chunk

    snapshots = _snapshots(asyncio.run(exercise()))
    assert snapshots[0].messages == []
    assert snapshots[0].user_interaction_state.text_input_state is TextInputState.SEND_DISABLED
    assert snapshots[0].user_interaction_state.thinking_state is not None
    assert snapshots[0].user_interaction_state.thinking_state.text == "Thinking"


def test_snapshot_follows_the_turn_status():
    message = MarkdownMessage(
        message_id="m_1",
        conversation_id="1",
        user_uuid="user-1",
        role=Role.agent,
        text="one",
        created_timestamp=datetime(2099, 1, 1, tzinfo=timezone.utc),
    )
    turn = Turn(
        turn_id="t_1",
        conversation_id="1",
        status=TurnStatus.queued,
        from_message="m_user",
    )

    def interaction(status: TurnStatus | None):
        current = None if status is None else turn.model_copy(update={"status": status})
        snapshot = _snapshots(format_conversation_sse("1", current, message))[0]
        return snapshot.user_interaction_state, snapshot.turn

    queued, queued_turn = interaction(TurnStatus.queued)
    assert queued.text_input_state is TextInputState.SEND_DISABLED
    assert queued.thinking_state is not None
    assert queued.thinking_state.text == "Thinking"
    assert queued_turn is not None and len(queued_turn.processing) == 1

    running, running_turn = interaction(TurnStatus.running)
    assert running.text_input_state is TextInputState.SEND_ENABLED_WITH_STOP_BUTTON
    assert running.thinking_state is not None
    assert running.thinking_state.text == "Thinking"
    assert running_turn is not None and len(running_turn.processing) == 1

    completed, completed_turn = interaction(TurnStatus.completed)
    assert completed.text_input_state is TextInputState.ENABLED
    assert completed.thinking_state is None
    assert completed_turn is not None and completed_turn.processing == []

    cancelled, cancelled_turn = interaction(TurnStatus.cancelled)
    assert cancelled.text_input_state is TextInputState.ENABLED
    assert cancelled.thinking_state is None
    assert cancelled_turn is not None and cancelled_turn.processing == []

    failed, _failed_turn = interaction(TurnStatus.failed)
    assert failed.thinking_state is not None
    assert failed.thinking_state.text == "Failed"

    timed_out, _timed_out_turn = interaction(TurnStatus.timeout)
    assert timed_out.thinking_state is not None
    assert timed_out.thinking_state.text == "Timed out"

    missing, missing_turn = interaction(None)
    assert missing.text_input_state is TextInputState.ENABLED
    assert missing.thinking_state is None
    assert missing_turn is not None and missing_turn.processing == []
