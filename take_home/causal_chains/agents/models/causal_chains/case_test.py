from datetime import datetime, timezone
from uuid import UUID

import pytest
from pydantic import ValidationError

from take_home.causal_chains.agents.models.causal_chains.case import Case


CASE_ID = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
CREATED = datetime(2026, 10, 1, tzinfo=timezone.utc)


def _case(case_id: UUID = CASE_ID) -> Case:
    return Case(
        case_id=case_id,
        conversation_id="1",
        from_message_id="m_1",
        created_timestamp=CREATED,
        updated_timestamp=CREATED,
    )


def test_case_is_an_id():
    case = _case()
    assert case.case_id == CASE_ID
    assert case.conversation_id == "1"
    assert case.from_message_id == "m_1"
    assert case.created_timestamp == CREATED
    assert case.updated_timestamp == CREATED
    assert case.model_dump(mode="json") == {
        "case_id": str(CASE_ID),
        "conversation_id": "1",
        "from_message_id": "m_1",
        "created_timestamp": "2026-10-01T00:00:00Z",
        "updated_timestamp": "2026-10-01T00:00:00Z",
    }


def test_case_rejects_extra_fields():
    with pytest.raises(ValidationError):
        Case.model_validate({"case_id": str(CASE_ID), "desc": "hormuz"})


def test_case_rejects_the_nil_id():
    with pytest.raises(ValidationError, match="case id is missing"):
        _case(UUID(int=0))
