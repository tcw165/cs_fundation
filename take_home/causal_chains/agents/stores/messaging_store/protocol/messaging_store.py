from datetime import datetime
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
        after_message_timestamp: datetime | None = None,
    ) -> MessagePage:
        """List one page of messages, oldest first.

        Args:
            conversation_id: Conversation to read.
            limit: Maximum number of messages in the page.
            after_message: Exclusive message id. The page starts after this
                message and does not include it. None starts at the oldest
                message.
            after_message_timestamp: created_timestamp of after_message. None
                when after_message is None. With the message id it is the
                sort key MSG#{timestamp}#{message_id}.
        """
        ...

    async def search_messages(
        self,
        conversation_id: str,
        since: datetime,
        until: datetime,
    ) -> list[Message]:
        """Messages in the window, oldest first.

        Args:
            conversation_id: Conversation to read.
            since: Inclusive start. A message at this timestamp is included.
            until: Inclusive end. A message at this timestamp is included.
        """
        ...

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

    async def get_conversation(
        self,
        conversation_id: str,
    ) -> Conversation | None:
        """The stored conversation, or none when it has not been created."""
        ...
