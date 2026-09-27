from decimal import Decimal

import pytest

from take_home.causal_chains.agents.models.causal_chains.likelihood import Likelihood, likelihood


def test_likelihood_docstring_names_the_buckets():
    assert Likelihood.__doc__ is not None
    assert "0.25" in Likelihood.__doc__
    assert likelihood.__doc__ is not None


def test_bucket_boundaries():
    assert likelihood(Decimal("0.08")) is Likelihood.very_unlikely
    assert likelihood(Decimal("0.25")) is Likelihood.unlikely
    assert likelihood(Decimal("0.50")) is Likelihood.likely
    assert likelihood(Decimal("0.75")) is Likelihood.very_likely


def test_p_outside_range_rejected():
    with pytest.raises(ValueError, match="outside 0 to 1"):
        likelihood(Decimal("1.01"))
