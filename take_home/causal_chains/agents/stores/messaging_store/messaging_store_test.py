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
    ) -> list[dict[str, object]]:
        rows = [
            item
            for (stored_table, _), item in self._items.items()
            if stored_table == table_name
            and item.get(key_name) == key_value
            and str(item.get(sk_name, "")).startswith(sk_prefix)
        ]
        rows.sort(key=lambda row: str(row.get(sk_name, "")))
        return rows

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
        seeded = await store.list_messages("1")
        missing = await store.list_messages("missing")
        return seeded, missing

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
        listed = await store.list_messages("1")
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
        listed = await store.list_messages("1")
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
