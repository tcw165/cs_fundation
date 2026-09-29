from uuid import UUID

from take_home.causal_chains.agents.models.causal_chains.case import Case
from take_home.causal_chains.agents.models.messaging.deeplink_card import (
    DeeplinkCard,
    DeeplinkRequest,
    DeeplinkResult,
)


CASE_ID = UUID("22222222-2222-4222-8222-222222222222")


def _card() -> DeeplinkCard:
    return DeeplinkCard(
        title="now",
        subtitle="the present",
        scheme="",
        route=f"/chain/{CASE_ID}",
        params=[],
    )


def test_deeplink_card_fields():
    card = _card()
    assert card.model_dump(mode="json") == {
        "title": "now",
        "subtitle": "the present",
        "scheme": "",
        "route": f"/chain/{CASE_ID}",
        "params": [],
    }
    assert card.__class__.model_fields["route"].description == (
        "In-app path. A stored chain is /chain/<case_id>. Do not include a version."
    )


def test_deeplink_request_reads_the_case():
    request = DeeplinkRequest(
        case=Case(case_id=CASE_ID),
        destination_desc="Open the saved chain.",
    )
    assert request.case.case_id == CASE_ID
    assert "Do not invent a case id." in (
        DeeplinkRequest.model_fields["case"].description or ""
    )
    result = DeeplinkResult(deeplinks=[_card()])
    assert result.deeplinks[0].route == f"/chain/{CASE_ID}"
