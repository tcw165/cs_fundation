import asyncio

from take_home.causal_chains.agents.stores.messaging_store.messaging_store import (
    MessagingStoreImpl,
)
from take_home.causal_chains.agents.stores.messaging_store.protocol.messaging_store import (
    MessagingStore,
)
from take_home.causal_chains.models.message import Message


class _FakeDynamoDb:
    def __init__(self) -> None:
        self._items: dict[tuple[str, tuple[tuple[str, object], ...]], dict[str, object]] = {}
        self.put_item("conversation", {"conversation_id": "1", "messages": []})

    def put_item(
        self,
        table_name: str,
        item: dict[str, object],
    ) -> None:
        if "turn_id" in item and table_name == "turn":
            key = (("turn_id", item["turn_id"]),)
        else:
            key = (("conversation_id", item["conversation_id"]),)
        self._items[(table_name, key)] = item

    def get_item(
        self,
        table_name: str,
        key: dict[str, object],
    ) -> dict[str, object] | None:
        stored_key = tuple(sorted(key.items()))
        return self._items.get((table_name, stored_key))


def test_messaging_store_impl_is_a_messaging_store():
    assert isinstance(MessagingStoreImpl(_FakeDynamoDb()), MessagingStore)


def test_list_messages_is_empty_for_seeded_conversation_and_missing_item():
    async def exercise():
        store = MessagingStoreImpl(_FakeDynamoDb())
        seeded = await store.list_messages("1")
        missing = await store.list_messages("missing")
        return seeded, missing

    seeded, missing = asyncio.run(exercise())
    assert seeded == []
    assert missing == []


def test_append_and_list_messages_by_conversation():
    async def exercise():
        database = _FakeDynamoDb()
        store = MessagingStoreImpl(database)
        hello = Message(
            message_id="m_1",
            conversation_id="1",
            turn_id="t_1",
            role="user",
            text="hello",
        )
        other = Message(
            message_id="m_2",
            conversation_id="2",
            turn_id="t_2",
            role="user",
            text="other",
        )
        await store.append(hello)
        await store.append(other)
        listed = await store.list_messages("1")
        conversation = database.get_item("conversation", {"conversation_id": "1"})
        return listed, conversation, hello

    listed, conversation, hello = asyncio.run(exercise())
    assert listed == [hello]
    assert conversation is not None
    assert "ttl" not in conversation
