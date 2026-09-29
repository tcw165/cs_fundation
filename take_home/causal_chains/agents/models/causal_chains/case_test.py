from uuid import UUID

import pytest
from pydantic import ValidationError

from take_home.causal_chains.agents.models.causal_chains.case import Case


CASE_ID = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")


def test_case_is_an_id():
    case = Case(case_id=CASE_ID)
    assert case.case_id == CASE_ID
    assert case.model_dump(mode="json") == {"case_id": str(CASE_ID)}


def test_case_rejects_extra_fields():
    with pytest.raises(ValidationError):
        Case.model_validate({"case_id": str(CASE_ID), "desc": "hormuz"})


def test_case_rejects_the_nil_id():
    with pytest.raises(ValidationError, match="case id is missing"):
        Case(case_id=UUID(int=0))
