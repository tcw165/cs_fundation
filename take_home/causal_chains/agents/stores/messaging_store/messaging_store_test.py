import asyncio
from datetime import datetime, timezone

from take_home.causal_chains.agents.stores.messaging_store.messaging_store import (
    MessagingStoreImpl,
)
from take_home.causal_chains.agents.stores.messaging_store.protocol.messaging_store import (
    MessagingStore,
)
from take_home.causal_chains.agents.models.messaging.message import (
    MarkdownMessage,
    Role,
)
from take_home.causal_chains.agents.models.messaging.message_widgets import (
    DeeplinkCardMessage,
)


class _FakeDynamoDb:
    def __init__(self) -> None:
        self._items: dict[tuple[str, tuple[tuple[str, object], ...]], dict[str, object]] = {}

    def put_item(
        self,
        table_name: str,
        item: dict[str, object],
    ) -> None:
        key = (("PK", item["PK"]), ("SK", item["SK"]))
        self._items[(table_name, key)] = item

    def get_item(
        self,
        table_name: str,
        key: dict[str, object],
    ) -> dict[str, object] | None:
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


def test_messaging_store_impl_is_a_messaging_store():
    assert isinstance(MessagingStoreImpl(_FakeDynamoDb(), "user-1"), MessagingStore)


def test_list_messages_is_empty_for_seeded_conversation_and_missing_item():
    async def exercise():
        store = MessagingStoreImpl(_FakeDynamoDb(), "user-1")
        seeded = await store.list_messages("1", 20)
        missing = await store.list_messages("missing", 20)
        return seeded.messages, missing.messages

    seeded, missing = asyncio.run(exercise())
    assert seeded == []
    assert missing == []


def test_append_and_list_messages_by_conversation():
    async def exercise():
        database = _FakeDynamoDb()
        store = MessagingStoreImpl(database, "user-1")
        hello = MarkdownMessage(
            message_id="m_1",
            conversation_id="1",
            user_uuid="user-1",
            role=Role.user,
            text="hello",
            created_timestamp=datetime(2026, 9, 30, tzinfo=timezone.utc),
        )
        other = MarkdownMessage(
            message_id="m_2",
            conversation_id="2",
            user_uuid="user-1",
            role=Role.user,
            text="other",
            created_timestamp=datetime(2026, 9, 30, tzinfo=timezone.utc),
        )
        card = DeeplinkCardMessage(
            message_id="m_3",
            conversation_id="1",
            user_uuid="user-1",
            role=Role.other,
            created_timestamp=datetime(2026, 9, 30, tzinfo=timezone.utc),
            title="now",
            subtitle="the present",
            link="/chain/now",
            enabled=True,
        )
        await store.append("1", hello)
        await store.append("2", other)
        await store.append("1", card)
        listed = (await store.list_messages("1", 20)).messages
        metadata = database.get_item(
            "conversation",
            {"PK": "CONV#1", "SK": "METADATA"},
        )
        message_item = database.get_item(
            "conversation",
            {"PK": hello.to_dynamodb()["PK"], "SK": hello.to_dynamodb()["SK"]},
        )
        return listed, metadata, message_item, hello, card

    listed, metadata, message_item, hello, card = asyncio.run(exercise())
    assert listed == [hello, card]
    assert metadata is not None
    assert metadata["SK"] == "METADATA"
    assert message_item is not None
    assert "time_to_live" not in message_item


def test_same_id_and_timestamp_replaces_one_message_and_keeps_metadata():
    async def exercise():
        database = _FakeDynamoDb()
        store = MessagingStoreImpl(database, "user-1")
        created = datetime(2026, 9, 30, tzinfo=timezone.utc)
        first = MarkdownMessage(
            message_id="m_1",
            conversation_id="1",
            user_uuid="user-1",
            role=Role.user,
            text="hello",
            created_timestamp=created,
        )
        second = MarkdownMessage(
            message_id="m_1",
            conversation_id="1",
            user_uuid="user-1",
            role=Role.user,
            text="hello again",
            created_timestamp=created,
        )
        await store.append("1", first)
        await store.append("1", second)
        listed = (await store.list_messages("1", 20)).messages
        metadata = database.get_item(
            "conversation",
            {"PK": "CONV#1", "SK": "METADATA"},
        )
        return listed, metadata

    listed, metadata = asyncio.run(exercise())
    assert [message.text for message in listed] == ["hello again"]
    assert metadata is not None
    assert metadata["SK"] == "METADATA"


def test_save_message_with_ttl_sets_time_to_live_and_list_conversations_uses_the_owner():
    async def exercise():
        database = _FakeDynamoDb()
        store = MessagingStoreImpl(database, "user-1")
        message = MarkdownMessage(
            message_id="m_1",
            conversation_id="1",
            user_uuid="user-1",
            role=Role.user,
            text="hello",
            created_timestamp=datetime(2026, 9, 30, tzinfo=timezone.utc),
        )
        await store.save_message_with_ttl("1", message, 1_700_000_000)
        item = database.get_item(
            "conversation",
            {"PK": message.to_dynamodb()["PK"], "SK": message.to_dynamodb()["SK"]},
        )
        conversations = await store.list_conversations("user-1")
        return item, conversations

    item, conversations = asyncio.run(exercise())
    assert item is not None
    assert item["time_to_live"] == 1_700_000_000
    assert [conversation.id for conversation in conversations] == ["1"]
    assert conversations[0].user_uuid == "user-1"


def test_search_messages_returns_the_inclusive_window_oldest_first():
    async def exercise():
        store = MessagingStoreImpl(_FakeDynamoDb(), "user-1")
        created = [
            datetime(2026, 9, 30, 1, tzinfo=timezone.utc),
            datetime(2026, 9, 30, 2, tzinfo=timezone.utc),
            datetime(2026, 9, 30, 3, tzinfo=timezone.utc),
            datetime(2026, 9, 30, 4, tzinfo=timezone.utc),
        ]
        for index, timestamp in enumerate(created):
            await store.append(
                "1",
                MarkdownMessage(
                    message_id=f"m_{index}",
                    conversation_id="1",
                    user_uuid="user-1",
                    role=Role.user,
                    text=f"text-{index}",
                    created_timestamp=timestamp,
                ),
            )
        await store.append(
            "2",
            MarkdownMessage(
                message_id="m_other",
                conversation_id="2",
                user_uuid="user-1",
                role=Role.user,
                text="other",
                created_timestamp=created[2],
            ),
        )
        window = await store.search_messages(
            conversation_id="1",
            since=created[1],
            until=created[2],
        )
        listed = (await store.list_messages("1", 20)).messages
        return window, listed

    window, listed = asyncio.run(exercise())
    assert [message.text for message in window] == ["text-1", "text-2"]
    assert [message.text for message in listed] == [
        "text-0",
        "text-1",
        "text-2",
        "text-3",
    ]


def test_list_messages_pages_oldest_first_and_a_short_page_has_no_cursor():
    async def exercise():
        store = MessagingStoreImpl(_FakeDynamoDb(), "user-1")
        created = [
            datetime(2026, 9, 30, 1, tzinfo=timezone.utc),
            datetime(2026, 9, 30, 2, tzinfo=timezone.utc),
            datetime(2026, 9, 30, 3, tzinfo=timezone.utc),
        ]
        for index, timestamp in enumerate(created):
            await store.append(
                "1",
                MarkdownMessage(
                    message_id=f"m_{index}",
                    conversation_id="1",
                    user_uuid="user-1",
                    role=Role.user,
                    text=f"text-{index}",
                    created_timestamp=timestamp,
                ),
            )
        first = await store.list_messages("1", 2)
        rest = await store.list_messages(
            "1",
            2,
            after_message=first.next_cursor,
            after_message_timestamp=first.messages[-1].created_timestamp,
        )
        short = await store.list_messages("1", 5)
        after_first = await store.list_messages(
            "1",
            20,
            after_message="m_0",
            after_message_timestamp=created[0],
        )
        missing = await store.list_messages(
            "1",
            20,
            after_message="missing",
            after_message_timestamp=created[0],
        )
        wrong_time = await store.list_messages(
            "1",
            20,
            after_message="m_0",
            after_message_timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
        return first, rest, short, after_first, missing, wrong_time

    first, rest, short, after_first, missing, wrong_time = asyncio.run(exercise())
    assert [message.text for message in first.messages] == ["text-0", "text-1"]
    assert first.next_cursor == "m_1"
    assert [message.text for message in rest.messages] == ["text-2"]
    assert rest.next_cursor is None
    assert short.next_cursor is None
    assert [message.message_id for message in after_first.messages] == ["m_1", "m_2"]
    assert [message.text for message in after_first.messages] == ["text-1", "text-2"]
    assert missing.messages == []
    assert wrong_time.messages == []
