from datetime import date
from decimal import Decimal

from coding.anrok_ai_programming.models.models import (
    IngestResult,
    RetrieveResult,
    TaxRatePeriod,
)


def _period(**overrides: object) -> TaxRatePeriod:
    values: dict[str, object] = {
        "locality_code": "9000",
        "locality_name": "HALEYVILLE",
        "county_number": "90",
        "tax_type": "ST",
        "rate_type": "GENER",
        "administered": "STATE",
        "active_date": date(2026, 1, 1),
        "inactive_date": None,
        "rate": Decimal("4.0000"),
        "indicator": "RC",
        "pj": "Y",
        "county_code": "7047",
        "pj_rate": Decimal("2.0000"),
    }
    values.update(overrides)
    return TaxRatePeriod.model_validate(values)


def test_period_round_trip() -> None:
    period = _period()
    assert TaxRatePeriod.model_validate_json(period.model_dump_json()) == period


def test_ingest_result_fields() -> None:
    result = IngestResult(
        rows_read=2,
        rows_written=2,
        table="tax_rate_period",
        endpoint="http://127.0.0.1:8002",
    )
    assert result.rows_written == 2


def test_shared_rate_collapses() -> None:
    result = RetrieveResult.from_periods(
        locality_code="9000",
        locality_name="HALEYVILLE",
        as_of=date(2026, 9, 28),
        tax_type="ST",
        rate_type="GENER",
        periods=[_period(), _period(county_code="7067")],
    )
    assert result.rate == Decimal("4.0000")
    assert result.pj_rate == Decimal("2.0000")
    assert result.rate_unit == "percent"
    assert len(result.periods) == 2


def test_disagreeing_rates_stay_on_periods() -> None:
    result = RetrieveResult.from_periods(
        locality_code="9000",
        locality_name="HALEYVILLE",
        as_of=date(2026, 9, 28),
        tax_type="ST",
        rate_type="GENER",
        periods=[_period(), _period(rate=Decimal("5.0000"))],
    )
    assert result.rate is None
    assert len(result.periods) == 2


def test_wdfee_rate_unit_is_flat() -> None:
    result = RetrieveResult.from_periods(
        locality_code="1",
        locality_name="BRIGHTON",
        as_of=date(2026, 9, 28),
        tax_type="ST",
        rate_type="WDFEE",
        periods=[_period(rate_type="WDFEE", rate=Decimal("250.0000"))],
    )
    assert result.rate_unit == "flat"
    assert result.rate == Decimal("250.0000")
