from uuid import UUID

import pytest
from pydantic import ValidationError

from take_home.causal_chains.agents.models.causal_chains.case import Case
from take_home.causal_chains.agents.models.causal_chains.now_scout_models import (
    NowScoutRequest,
)

CASE_ID = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")


def test_now_scout_request_keeps_the_case_and_future():
    request = NowScoutRequest(
        case=Case(case_id=CASE_ID),
        future="The Strait of Hormuz is going to open next week.",
    )
    assert request.case.case_id == CASE_ID
    assert request.model_dump(mode="json")["case"] == {"case_id": str(CASE_ID)}


def test_now_scout_request_rejects_an_empty_future():
    with pytest.raises(ValidationError, match="future is empty"):
        NowScoutRequest(case=Case(case_id=CASE_ID), future="  ")


def test_now_scout_request_rejects_the_nil_case():
    with pytest.raises(ValidationError, match="case id is missing"):
        NowScoutRequest(
            case={"case_id": "00000000-0000-0000-0000-000000000000"},
            future="open",
        )
