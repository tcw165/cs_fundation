from datetime import timedelta
from typing import Annotated

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
    async def search_conversation_messages(
        since_minutes_ago: Annotated[
            int,
            "Minutes before now where the window starts. A message at that time is included.",
        ],
        until_minutes_ago: Annotated[
            int,
            "Minutes before now where the window ends. 0 is the current time. A message at that time is included.",
        ],
    ) -> list[Message]:
        """Search the conversation for messages in a window before now, oldest first.

        Use this when you notice context missing from the messages you were given.
        """
        now = clock.now()
        return await messaging_store.search_messages(
            conversation_id=conversation_id,
            since=now - timedelta(minutes=since_minutes_ago),
            until=now - timedelta(minutes=until_minutes_ago),
        )

    @function_tool
    async def get_oldest_conversation_message() -> list[Message]:
        """The oldest stored message, including when it was created.

        An empty search can be older than this message. Use that to explain the gap.
        """
        page = await messaging_store.list_messages(
            conversation_id,
            limit=1,
        )
        return list(page.messages)

    return (search_conversation_messages, get_oldest_conversation_message)
