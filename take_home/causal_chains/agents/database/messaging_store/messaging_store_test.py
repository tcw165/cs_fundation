from take_home.causal_chains.agents.database.messaging_store.messaging_store import (
    InMemoryMessagingStore,
)
from take_home.causal_chains.agents.database.messaging_store.protocol.messaging_store import (
    MessagingStore,
)
from take_home.causal_chains.models.message import Message


def test_in_memory_store_is_a_messaging_store():
    assert isinstance(InMemoryMessagingStore(), MessagingStore)


def test_append_and_list_messages_by_conversation():
    store = InMemoryMessagingStore()
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
    store.append(hello)
    store.append(other)
    assert store.list_messages("1") == [hello]
