from decimal import Decimal

import pytest

from take_home.causal_chains.agents.models.causal_chain.evidence import Evidence
from take_home.causal_chains.agents.models.causal_chain.link_inputs import LinkInputs
from take_home.causal_chains.agents.models.causal_chain.price import normalize, raw_p


def test_empty_evidence_keeps_the_base_rate():
    got = raw_p(LinkInputs(base_rate=Decimal("0.25"), evidence=[]))
    assert abs(got - Decimal("0.25")) < Decimal("1e-12")


def test_positive_log_odds_raises_raw_p():
    base = LinkInputs(base_rate=Decimal("0.25"), evidence=[])
    shifted = LinkInputs(
        base_rate=Decimal("0.25"),
        evidence=[Evidence(note="deal announced", log_odds=Decimal("0.4"))],
    )
    assert raw_p(shifted) > raw_p(base)


def test_normalize_three_shares_sum_to_one():
    shares = normalize([Decimal("1"), Decimal("1"), Decimal("2")])
    assert shares == [Decimal("0.250000"), Decimal("0.250000"), Decimal("0.500000")]
    assert sum(shares, Decimal("0")) == Decimal("1.000000")


def test_normalize_rejects_a_zero_sum():
    with pytest.raises(ValueError, match="raw sum is 0"):
        normalize([Decimal("0"), Decimal("0")])


def test_raw_p_docstring_names_the_formula():
    assert raw_p.__doc__ is not None
    assert "sigmoid" in raw_p.__doc__
