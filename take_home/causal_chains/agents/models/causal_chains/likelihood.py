from decimal import Decimal
from enum import StrEnum


class Likelihood(StrEnum):
    """Coarse bucket for a probability in 0..1.

    very_unlikely is below 0.25, unlikely below 0.50, likely below 0.75,
    and very_likely is the rest. This labels a stored p. It does not price a link.
    """

    very_unlikely = "very_unlikely"
    unlikely = "unlikely"
    likely = "likely"
    very_likely = "very_likely"


def likelihood(p: Decimal) -> Likelihood:
    """Map a stored probability onto a Likelihood bucket."""
    if p < 0 or p > 1:
        raise ValueError("p is outside 0 to 1")
    if p < Decimal("0.25"):
        return Likelihood.very_unlikely
    if p < Decimal("0.50"):
        return Likelihood.unlikely
    if p < Decimal("0.75"):
        return Likelihood.likely
    return Likelihood.very_likely
