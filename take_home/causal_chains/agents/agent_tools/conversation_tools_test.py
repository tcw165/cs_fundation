import asyncio
import json
from datetime import datetime, timedelta, timezone

from agents.tool_context import ToolContext

from take_home.causal_chains.agents.agent_tools.conversation_tools import (
    build_conversation_tools,
)
from take_home.causal_chains.agents.models.messaging.message import MarkdownMessage, Role
from take_home.causal_chains.agents.models.run_clients import RunClients
from take_home.causal_chains.agents.models.run_context import RunContext


class _FixedClock:
    def now(self) -> datetime:
        return datetime(2026, 9, 30, 1, 10, tzinfo=timezone.utc)


class _Store:
    def __init__(self) -> None:
        self.calls: list[tuple[str, datetime, datetime]] = []

    async def search_messages(
        self,
        conversation_id: str,
        since: datetime,
        until: datetime,
    ) -> list[MarkdownMessage]:
        self.calls.append((conversation_id, since, until))
        return [
            MarkdownMessage(
                message_id="m_1",
                conversation_id=conversation_id,
                user_uuid="user-1",
                role=Role.user,
                text="hormuz",
                created_timestamp=since,
            ),
        ]


def test_search_messages_uses_minutes_before_now():
    clock = _FixedClock()
    store = _Store()
    tool = build_conversation_tools(
        conversation_id="1",
        messaging_store=store,
        clock=clock,
    )[0]
    context = RunContext(
        conversation_id="1",
        clock=clock,
        turn_id="t_1",
        clients=RunClients(causal_chain_store=object()),
    )
    payload = json.dumps({"since_minutes_ago": 15, "until_minutes_ago": 5})

    async def exercise() -> object:
        return await tool.on_invoke_tool(
            ToolContext(
                context=context,
                tool_name=tool.name,
                tool_call_id="call_1",
                tool_arguments=payload,
            ),
            payload,
        )

    result = asyncio.run(exercise())
    now = clock.now()
    assert tool.name == "search_messages"
    assert store.calls == [
        ("1", now - timedelta(minutes=15), now - timedelta(minutes=5)),
    ]
    assert [message.text for message in result] == ["hormuz"]
