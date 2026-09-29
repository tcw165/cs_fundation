from uuid import UUID

from take_home.causal_chains.agents.models.messaging.deeplink_card import DeeplinkCard
from take_home.causal_chains.agents.models.messaging.message import Role, message_adapter
from take_home.causal_chains.agents.models.messaging.message_widgets import (
    DeeplinkCardMessage,
    card_link,
    deeplink_message,
)


CASE_ID = UUID("22222222-2222-4222-8222-222222222222")


def _card() -> DeeplinkCard:
    return DeeplinkCard(
        title="now",
        subtitle="the present",
        scheme="",
        route=f"/chain/{CASE_ID}",
        params={},
    )


def test_card_link_keeps_an_in_app_path():
    assert card_link(_card()) == f"/chain/{CASE_ID}"


def test_card_link_adds_a_scheme_and_query():
    card = _card().model_copy(
        update={"scheme": "app", "route": "chain/1", "params": {"title": "now"}},
    )
    assert card_link(card) == "app://chain/1?title=now"


def test_deeplink_message_copies_the_card():
    message = deeplink_message(_card())
    assert message.role is Role.other
    assert message.title == "now"
    assert message.subtitle == "the present"
    assert message.link == f"/chain/{CASE_ID}"
    assert message.enabled is True
    restored = message_adapter.validate_python(message.model_dump())
    assert isinstance(restored, DeeplinkCardMessage)
    assert restored == message
