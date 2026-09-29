import uuid
from typing import Literal
from urllib.parse import urlencode

from take_home.causal_chains.agents.models.messaging.deeplink_card import DeeplinkCard
from take_home.causal_chains.agents.models.messaging.message import BaseMessage, Role


class DeeplinkCardMessage(BaseMessage):
    """A chat message that shows one deeplink card."""

    type: Literal["deeplink"] = "deeplink"
    title: str
    subtitle: str
    link: str
    enabled: bool


def card_link(card: DeeplinkCard) -> str:
    """Build the message link from scheme, route, and params."""
    query = urlencode(card.params)
    if card.scheme:
        base = f"{card.scheme}://{card.route.lstrip('/')}"
    else:
        base = card.route if card.route.startswith("/") else f"/{card.route}"
    return f"{base}?{query}" if query else base


def deeplink_message(card: DeeplinkCard) -> DeeplinkCardMessage:
    """Copy the card onto a chat message. enabled is True."""
    return DeeplinkCardMessage(
        message_id=str(uuid.uuid4()),
        role=Role.other,
        title=card.title,
        subtitle=card.subtitle,
        link=card_link(card),
        enabled=True,
    )
