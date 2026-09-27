from typing import Protocol

from take_home.causal_chains.models.message import Message


class MessagingStore(Protocol):
    def append(self, message: Message) -> None: ...

    def list_messages(self, conversation_id: str) -> list[Message]: ...
