from typing import override

from take_home.causal_chains.agents.clients.dynamo_db.protocol.protocol import DynamoDb
from take_home.causal_chains.agents.stores.messaging_store.protocol.messaging_store import (
    MessagingStore,
)
from take_home.causal_chains.agents.models.messaging.message import Message


class MessagingStoreImpl(MessagingStore):
    def __init__(
        self,
        dynamo_db: DynamoDb,
    ) -> None:
        self._dynamo_db = dynamo_db

    @override
    async def append(
        self,
        message: Message,
    ) -> None:
        current = self._dynamo_db.get_item(
            "conversation",
            {"conversation_id": message.conversation_id},
        )
        messages = [] if current is None else list(current["messages"])
        messages.append(message.model_dump())
        self._dynamo_db.put_item(
            "conversation",
            {
                "conversation_id": message.conversation_id,
                "messages": messages,
            },
        )

    @override
    async def list_messages(
        self,
        conversation_id: str,
    ) -> list[Message]:
        current = self._dynamo_db.get_item(
            "conversation",
            {"conversation_id": conversation_id},
        )
        if current is None:
            return []
        return [Message.model_validate(item) for item in current["messages"]]
