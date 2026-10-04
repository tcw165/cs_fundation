import asyncio
import json
from datetime import datetime, timedelta, timezone

from agents.tool_context import ToolContext

from take_home.causal_chains.agents.agent_tools.conversation_tools import (
    build_conversation_tools,
)
from take_home.causal_chains.agents.models.messaging.message import MarkdownMessage, Role
from take_home.causal_chains.agents.stores.messaging_store.protocol.message_page import (
    MessagePage,
)
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
    assert tool.name == "search_conversation_messages"
    assert "Search the conversation" in tool.description
    assert "context missing" in tool.description
    properties = tool.params_json_schema["properties"]
    assert "window starts" in properties["since_minutes_ago"]["description"]
    assert "current time" in properties["until_minutes_ago"]["description"]
    assert "default" not in properties["until_minutes_ago"]
    assert "until_minutes_ago" in tool.params_json_schema["required"]
    assert store.calls == [
        ("1", now - timedelta(minutes=15), now - timedelta(minutes=5)),
    ]
    assert [message.text for message in result] == ["hormuz"]


def test_oldest_conversation_message_is_the_first_page():
    created = datetime(2026, 9, 28, tzinfo=timezone.utc)
    later = datetime(2026, 9, 30, tzinfo=timezone.utc)
    oldest = MarkdownMessage(
        message_id="m_old",
        conversation_id="1",
        user_uuid="user-1",
        role=Role.user,
        text="first",
        created_timestamp=created,
    )
    newer = oldest.model_copy(
        update={"message_id": "m_new", "text": "later", "created_timestamp": later},
    )

    class _Paged:
        def __init__(self) -> None:
            self.limits: list[int] = []

        async def list_messages(
            self,
            conversation_id: str,
            limit: int,
            after_message: str | None = None,
            after_message_timestamp: datetime | None = None,
        ) -> MessagePage:
            self.limits.append(limit)
            assert conversation_id == "1"
            assert after_message is None
            return MessagePage(messages=[oldest, newer][:limit])

    clock = _FixedClock()
    store = _Paged()
    tool = build_conversation_tools(
        conversation_id="1",
        messaging_store=store,
        clock=clock,
    )[1]
    context = RunContext(
        conversation_id="1",
        clock=clock,
        turn_id="t_1",
        clients=RunClients(causal_chain_store=object()),
    )

    async def exercise() -> object:
        return await tool.on_invoke_tool(
            ToolContext(
                context=context,
                tool_name=tool.name,
                tool_call_id="call_2",
                tool_arguments="{}",
            ),
            "{}",
        )

    result = asyncio.run(exercise())
    assert tool.name == "get_oldest_conversation_message"
    assert "oldest stored message" in tool.description
    assert "explain the gap" in tool.description
    assert tool.params_json_schema["properties"] == {}
    assert store.limits == [1]
    assert result == [oldest]
