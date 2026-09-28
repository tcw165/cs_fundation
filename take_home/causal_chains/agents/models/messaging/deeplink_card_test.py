from uuid import UUID

from take_home.causal_chains.agents.models.messaging.deeplink_card import DeeplinkCard


NOW_ID = UUID("11111111-1111-4111-8111-111111111111")


def test_deeplink_card_fields():
    card = DeeplinkCard(
        title="now",
        root_situation_id=NOW_ID,
        root_version=1,
    )
    assert card.model_dump(mode="json") == {
        "title": "now",
        "root_situation_id": str(NOW_ID),
        "root_version": 1,
    }
