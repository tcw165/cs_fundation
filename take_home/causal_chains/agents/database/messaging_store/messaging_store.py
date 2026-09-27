from typing import override

from take_home.causal_chains.agents.database.messaging_store.protocol.messaging_store import (
    MessagingStore,
)
from take_home.causal_chains.models.message import Message


class InMemoryMessagingStore(MessagingStore):
    def __init__(self) -> None:
        self._messages: list[Message] = []

    @override
    def append(self, message: Message) -> None:
        self._messages.append(message)

    @override
    def list_messages(self, conversation_id: str) -> list[Message]:
        return [
            message
            for message in self._messages
            if message.conversation_id == conversation_id
        ]
