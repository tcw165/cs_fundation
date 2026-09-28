from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict


class TaxRatePeriod(BaseModel):
    model_config = ConfigDict(extra="forbid")

    locality_code: str
    locality_name: str
    county_number: str
    tax_type: str
    rate_type: str
    administered: str
    active_date: date
    inactive_date: date | None
    rate: Decimal
    indicator: str
    pj: str | None
    county_code: str
    pj_rate: Decimal | None


class IngestResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rows_read: int
    rows_written: int
    table: str
    endpoint: str


class RetrieveResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    locality_code: str
    locality_name: str
    as_of: date
    tax_type: str
    rate_type: str
    rate: Decimal | None
    pj_rate: Decimal | None
    periods: list[TaxRatePeriod]
    rate_unit: Literal["percent", "flat"]

    @classmethod
    def from_periods(
        cls,
        *,
        locality_code: str,
        locality_name: str,
        as_of: date,
        tax_type: str,
        rate_type: str,
        periods: list[TaxRatePeriod],
    ) -> "RetrieveResult":
        return cls(
            locality_code=locality_code,
            locality_name=locality_name,
            as_of=as_of,
            tax_type=tax_type,
            rate_type=rate_type,
            rate=_shared(periods, "rate"),
            pj_rate=_shared(periods, "pj_rate"),
            periods=periods,
            rate_unit="flat" if rate_type == "WDFEE" else "percent",
        )


def _shared(periods: list[TaxRatePeriod], field_name: str) -> Decimal | None:
    if not periods:
        return None
    values = [getattr(period, field_name) for period in periods]
    first = values[0]
    if any(value != first for value in values):
        return None
    return first
