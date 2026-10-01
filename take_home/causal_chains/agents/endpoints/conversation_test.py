import asyncio
from datetime import datetime, timezone

from take_home.causal_chains.agents.chat_service.chat_service import ChatService
from take_home.causal_chains.agents.endpoints.conversation import post_message, turn_sse
from take_home.causal_chains.agents.http_models.post_message_body import PostMessageBody
from take_home.causal_chains.agents.models.messaging.message import (
    MarkdownMessage,
    Role,
)
from take_home.causal_chains.agents.models.messaging.turn_status import TurnStatus
from take_home.causal_chains.agents.models.run_context import RunContext
from take_home.causal_chains.agents.stores.messaging_store.messaging_store import (
    MessagingStoreImpl,
)
from take_home.causal_chains.agents.stores.turn_store.turn_store import InMemoryTurnStore


class _ChainStore:
    pass


class _FixedClock:
    def now(self) -> datetime:
        return datetime(2026, 9, 29, 5, 16, tzinfo=timezone.utc)


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


class _Scripted:
    def __init__(self) -> None:
        self.calls = 0
        self.contexts: list[RunContext] = []

    async def stream(self, inputs: list[str], context: RunContext):
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
    store = MessagingStoreImpl(_FakeDynamoDb())
    turn_store = InMemoryTurnStore()
    runner = _Scripted()
    service = ChatService(runner, store, turn_store, _ChainStore(), _FixedClock())
    return _Container(service, store, turn_store), runner, store, turn_store


async def _read_sse(
    container: _Container,
    turn_id: str,
    after_message: str,
    include_traces: bool = False,
) -> str:
    response = await turn_sse(
        "1",
        turn_id,
        container,
        after_message=after_message,
        include_traces=include_traces,
    )
    chunks: list[str] = []
    async for chunk in response.body_iterator:
        chunks.append(chunk if isinstance(chunk, str) else chunk.decode())
    return "".join(chunks)


def test_post_message_stores_the_anchored_turn():
    async def exercise():
        container, _runner, store, turn_store = _services()
        turn = await post_message("1", PostMessageBody(text="hello"), container)
        stored = await store.list_messages("1")
        saved = await turn_store.get_turn(turn.turn_id)
        return turn, stored, saved

    turn, stored, saved = asyncio.run(exercise())
    assert turn.status is TurnStatus.queued
    assert len(stored) == 1
    assert isinstance(stored[0], MarkdownMessage)
    assert stored[0].role is Role.user
    assert stored[0].text == "hello"
    assert turn.from_message == stored[0].message_id
    assert saved is not None
    assert saved.from_message == stored[0].message_id
    assert saved.status is TurnStatus.queued


def test_sse_forwards_runner_messages_after_the_cursor():
    async def exercise():
        container, runner, _store, turn_store = _services()
        turn = await post_message("1", PostMessageBody(text="hello"), container)
        everything = await _read_sse(container, turn.turn_id, "")
        saved = await turn_store.get_turn(turn.turn_id)
        replay = await _read_sse(container, turn.turn_id, "")

        user_container, user_runner, _store_again, _turns_again = _services()
        queued = await post_message("1", PostMessageBody(text="hello"), user_container)
        from_user = await _read_sse(
            user_container,
            queued.turn_id,
            queued.from_message,
            include_traces=True,
        )

        skip_container, _skip_runner, _skip_store, _skip_turns = _services()
        later = await post_message("1", PostMessageBody(text="hello"), skip_container)
        skipped = await _read_sse(skip_container, later.turn_id, "m_a")
        return (
            everything,
            replay,
            from_user,
            skipped,
            saved,
            runner,
            user_runner,
            queued.from_message,
        )

    (
        everything,
        replay,
        from_user,
        skipped,
        saved,
        runner,
        user_runner,
        from_message,
    ) = asyncio.run(exercise())
    assert '"text":"one"' in everything
    assert '"text":"two"' in everything
    assert saved is not None
    assert saved.status is TurnStatus.completed
    assert saved.from_message
    assert runner.calls == 1
    assert replay == ""
    assert '"text":"one"' in from_user
    assert '"text":"two"' in from_user
    assert from_message not in from_user
    assert user_runner.calls == 1
    assert user_runner.contexts[0].run_config.include_traces is True
    assert "m_a" not in skipped
    assert '"text":"two"' in skipped
