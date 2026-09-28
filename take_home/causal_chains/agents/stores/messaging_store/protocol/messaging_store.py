from typing import Protocol, runtime_checkable

from take_home.causal_chains.agents.models.messaging.message import Message


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
    ) -> list[Message]: ...
