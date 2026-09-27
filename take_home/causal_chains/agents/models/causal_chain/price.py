from decimal import Decimal

from take_home.causal_chains.agents.models.causal_chain.link_inputs import LinkInputs

_SHARE = Decimal("0.000001")


def raw_p(inputs: LinkInputs) -> Decimal:
    """Probability implied by the inputs, before sibling normalization.

    This is sigmoid(logit(base_rate) + sum(log_odds)). The pricer never
    writes p. Sibling shares are a separate step.
    """
    shift = sum((item.log_odds for item in inputs.evidence), Decimal("0"))
    return _sigmoid(_logit(inputs.base_rate) + shift)


def normalize(raw_values: list[Decimal]) -> list[Decimal]:
    """Turn sibling raw probabilities into shares that sum to 1.

    The last share absorbs rounding so the total is exactly 1.
    An empty list stays empty. A zero sum is rejected.
    """
    if not raw_values:
        return []
    total = sum(raw_values, Decimal("0"))
    if total == 0:
        raise ValueError("raw sum is 0")
    shares = [(value / total).quantize(_SHARE) for value in raw_values]
    drift = Decimal("1.000000") - sum(shares, Decimal("0"))
    shares[-1] = (shares[-1] + drift).quantize(_SHARE)
    return shares


def _logit(p: Decimal) -> Decimal:
    return (p / (Decimal(1) - p)).ln()


def _sigmoid(x: Decimal) -> Decimal:
    return Decimal(1) / (Decimal(1) + (-x).exp())
