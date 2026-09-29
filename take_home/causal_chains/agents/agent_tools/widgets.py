from agents import RunContextWrapper, function_tool

from take_home.causal_chains.agents.models.messaging.deeplink_card import DeeplinkCard
from take_home.causal_chains.agents.models.run_context import RunContext


@function_tool
async def make_deeplink_widget(
    ctx: RunContextWrapper[RunContext],
    card: DeeplinkCard,
    render_at_end: bool = True,
) -> DeeplinkCard:
    """Show a deeplink card.

    Args:
        ctx: Run context.
        card: The card to show. Use the title, subtitle, scheme, route, and params that came back.
        render_at_end: When true, the reader sees the card after the rest of this turn. When false, the reader sees it now.
    """
    del ctx, render_at_end
    return card
