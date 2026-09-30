import asyncio
import json
from datetime import datetime, timezone

from agents.tool_context import ToolContext

from take_home.causal_chains.agents.agent_tools.widgets import show_deeplink_widget
from take_home.causal_chains.agents.models.messaging.deeplink_card import (
    DEEPLINK_SCHEME,
    DeeplinkCard,
)
from take_home.causal_chains.agents.models.run_clients import RunClients
from take_home.causal_chains.agents.models.run_context import RunContext


class _FixedClock:
    def now(self) -> datetime:
        return datetime(2026, 9, 29, 5, 16, tzinfo=timezone.utc)


def _card() -> DeeplinkCard:
    return DeeplinkCard(
        title="now",
        subtitle="the present",
        scheme=DEEPLINK_SCHEME,
        route="/chain/case",
        params=[],
    )


def _invoke(arguments: dict[str, object]) -> DeeplinkCard:
    payload = json.dumps(arguments)
    context = RunContext(
        conversation_id="1",
        clock=_FixedClock(),
        turn_id="t_1",
        clients=RunClients(causal_chain_store=object()),
    )

    async def exercise() -> object:
        return await show_deeplink_widget.on_invoke_tool(
            ToolContext(
                context=context,
                tool_name=show_deeplink_widget.name,
                tool_call_id="call_1",
                tool_arguments=payload,
            ),
            payload,
        )

    result = asyncio.run(exercise())
    assert isinstance(result, DeeplinkCard)
    return result


def test_show_deeplink_widget_returns_the_card():
    card = _card()
    assert _invoke({"card": card.model_dump(mode="json")}) == card
    assert "deeplink card" in show_deeplink_widget.description
    rendered = show_deeplink_widget.params_json_schema["properties"]["render_at_end"]
    assert rendered["default"] is True
    assert "after the rest of this turn" in rendered["description"]
