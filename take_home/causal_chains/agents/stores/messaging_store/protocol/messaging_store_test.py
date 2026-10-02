from datetime import datetime, timezone

from take_home.causal_chains.agents.stores.messaging_store.protocol.messaging_store import (
    MessagingStore,
)
from take_home.causal_chains.agents.models.messaging.conversation import Conversation
from take_home.causal_chains.agents.models.messaging.message import (
    MarkdownMessage,
    Message,
    Role,
)
from take_home.causal_chains.agents.stores.messaging_store.protocol.message_page import (
    MessagePage,
)


class _Both:
    async def append(
        self,
        conversation_id: str,
        message: Message,
    ) -> None:
        return None

    async def list_messages(
        self,
        conversation_id: str,
        limit: int,
        after_message: str | None = None,
        after_message_timestamp: datetime | None = None,
    ) -> MessagePage:
        return MessagePage(messages=[])

    async def save_message_with_ttl(
        self,
        conversation_id: str,
        message: Message,
        time_to_live: int,
    ) -> None:
        return None

    async def list_conversations(
        self,
        user_uuid: str,
    ) -> list[Conversation]:
        return []


class _AppendOnly:
    async def append(
        self,
        conversation_id: str,
        message: Message,
    ) -> None:
        return None


def test_messaging_store_requires_append_and_list_messages():
    assert isinstance(_Both(), MessagingStore)
    assert not isinstance(_AppendOnly(), MessagingStore)


def test_message_fields_for_store():
    message = MarkdownMessage(
        message_id="m_1",
        conversation_id="1",
        user_uuid="user-1",
        role=Role.user,
        text="hello",
        created_timestamp=datetime(2026, 9, 30, tzinfo=timezone.utc),
    )
    assert message.role is Role.user
    assert message.text == "hello"
