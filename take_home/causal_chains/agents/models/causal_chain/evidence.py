from decimal import Decimal

from pydantic import BaseModel, field_validator


class Evidence(BaseModel):
    """One signed shift applied to a link's base rate.

    log_odds is clamped to -2..2 so one note cannot swamp the base rate.
    Positive log_odds makes the effect more likely.
    """

    note: str
    log_odds: Decimal

    @field_validator("log_odds")
    @classmethod
    def clamp_log_odds(cls, value: Decimal) -> Decimal:
        if value < Decimal("-2"):
            return Decimal("-2")
        if value > Decimal("2"):
            return Decimal("2")
        return value
