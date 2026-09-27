from decimal import Decimal
from enum import StrEnum


class Likelihood(StrEnum):
    very_unlikely = "very_unlikely"
    unlikely = "unlikely"
    likely = "likely"
    very_likely = "very_likely"


def likelihood(p: Decimal) -> Likelihood:
    if p < 0 or p > 1:
        raise ValueError("p is outside 0 to 1")
    if p < Decimal("0.25"):
        return Likelihood.very_unlikely
    if p < Decimal("0.50"):
        return Likelihood.unlikely
    if p < Decimal("0.75"):
        return Likelihood.likely
    return Likelihood.very_likely
