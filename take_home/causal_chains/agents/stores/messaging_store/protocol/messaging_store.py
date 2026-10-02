from typing import Protocol, runtime_checkable

from take_home.causal_chains.agents.models.messaging.conversation import Conversation
from take_home.causal_chains.agents.models.messaging.message import Message
from take_home.causal_chains.agents.stores.messaging_store.protocol.message_page import (
    MessagePage,
)


@runtime_checkable
class MessagingStore(Protocol):
    async def append(
        self,
        conversation_id: str,
        message: Message,
    ) -> None: ...

    async def list_messages(
        self,
        conversation_id: str,
        limit: int,
        after_message: str | None = None,
    ) -> MessagePage: ...

    async def save_message_with_ttl(
        self,
        conversation_id: str,
        message: Message,
        time_to_live: int,
    ) -> None: ...

    async def list_conversations(
        self,
        user_uuid: str,
    ) -> list[Conversation]: ...
