from take_home.causal_chains.agents.stores.messaging_store.protocol.messaging_store import (
    MessagingStore,
)
from take_home.causal_chains.agents.models.messaging.message import Message


class _Both:
    async def append(
        self,
        message: Message,
    ) -> None:
        return None

    async def list_messages(
        self,
        conversation_id: str,
    ) -> list[Message]:
        return []


class _AppendOnly:
    async def append(
        self,
        message: Message,
    ) -> None:
        return None


def test_messaging_store_requires_append_and_list_messages():
    assert isinstance(_Both(), MessagingStore)
    assert not isinstance(_AppendOnly(), MessagingStore)


def test_message_fields_for_store():
    message = Message(
        message_id="m_1",
        conversation_id="1",
        turn_id="t_1",
        role="user",
        text="hello",
    )
    assert message.conversation_id == "1"
    assert message.role == "user"
    assert message.text == "hello"
