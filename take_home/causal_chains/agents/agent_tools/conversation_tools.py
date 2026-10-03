from datetime import timedelta

from agents import FunctionTool, function_tool

from take_home.causal_chains.agents.models.messaging.message import Message
from take_home.causal_chains.agents.stores.messaging_store.protocol.messaging_store import (
    MessagingStore,
)
from take_home.causal_chains.time.protocol.protocol import Clock


def build_conversation_tools(
    conversation_id: str,
    messaging_store: MessagingStore,
    clock: Clock,
) -> tuple[FunctionTool, ...]:
    @function_tool
    async def search_messages(
        since_minutes_ago: int,
        until_minutes_ago: int = 0,
    ) -> list[Message]:
        """Messages from since_minutes_ago until until_minutes_ago before now.

        until_minutes_ago is 0 for up to the current time. Oldest first.
        """
        now = clock.now()
        return await messaging_store.search_messages(
            conversation_id=conversation_id,
            since=now - timedelta(minutes=since_minutes_ago),
            until=now - timedelta(minutes=until_minutes_ago),
        )

    return (search_messages,)
