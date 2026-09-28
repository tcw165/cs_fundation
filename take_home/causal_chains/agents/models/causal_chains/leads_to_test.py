from decimal import Decimal
from uuid import UUID

import pytest
from pydantic import ValidationError

from take_home.causal_chains.agents.models.causal_chains.input_variable import (
    InputVariable,
    probability,
)
from take_home.causal_chains.agents.models.causal_chains.leads_to import LeadsTo


NOW_ID = UUID("11111111-1111-4111-8111-111111111111")
DEAL_ID = UUID("22222222-2222-4222-8222-222222222222")


def test_leads_to_keeps_decimal_p():
    edge = LeadsTo(
        from_situation_id=NOW_ID,
        from_version=1,
        to_situation_id=DEAL_ID,
        to_version=1,
        p=Decimal("0.08"),
    )
    assert edge.p == Decimal("0.08")


def test_p_outside_zero_to_one_rejected():
    with pytest.raises(ValidationError):
        LeadsTo(
            from_situation_id=NOW_ID,
            from_version=1,
            to_situation_id=DEAL_ID,
            to_version=1,
            p=Decimal("1.01"),
        )
    with pytest.raises(ValidationError):
        LeadsTo(
            from_situation_id=NOW_ID,
            from_version=1,
            to_situation_id=DEAL_ID,
            to_version=1,
            p=Decimal("-0.01"),
        )


def test_self_edge_rejected():
    with pytest.raises(ValidationError, match="self-edge"):
        LeadsTo(
            from_situation_id=NOW_ID,
            from_version=1,
            to_situation_id=NOW_ID,
            to_version=1,
            p=Decimal("1"),
        )


def test_p_is_the_mean_of_the_inputs():
    inputs = [
        InputVariable(name="deal_odds", value=Decimal("0.10")),
        InputVariable(name="clearance", value=Decimal("0.06")),
    ]
    assert probability(inputs) == Decimal("0.0800")
    edge = LeadsTo(
        from_situation_id=NOW_ID,
        from_version=1,
        to_situation_id=DEAL_ID,
        to_version=1,
        inputs=inputs,
        p=Decimal("0.0800"),
    )
    assert edge.p == Decimal("0.08")


def test_p_that_disagrees_with_inputs_rejected():
    with pytest.raises(ValidationError, match="probability of the inputs"):
        LeadsTo(
            from_situation_id=NOW_ID,
            from_version=1,
            to_situation_id=DEAL_ID,
            to_version=1,
            inputs=[InputVariable(name="deal_odds", value=Decimal("0.10"))],
            p=Decimal("0.08"),
        )
