from datetime import date
from decimal import Decimal

from coding.anrok_ai_programming.models.models import TaxRatePeriod
from coding.anrok_ai_programming.store.dynamo_db.dynamo_db import (
    DynamoTaxRateStore,
    ensure_local_endpoint,
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


def test_replace_all_nukes_previous_rows_and_query_finds_the_open_rate() -> None:
    store = DynamoTaxRateStore(ensure_local_endpoint())
    store.replace_all(
        [
            _period(inactive_date=date(2025, 12, 31), rate=Decimal("3.0000"), county_code="7001"),
            _period(),
            _period(county_code="7067"),
        ]
    )
    found = store.find_in_force("haleyville", date(2026, 9, 28), "ST", "GENER")
    assert found.rate == Decimal("4.0000")
    assert found.pj_rate == Decimal("2.0000")
    assert found.locality_code == "9000"
    assert {period.county_code for period in found.periods} == {"7047", "7067"}

    nuked = store.replace_all([_period(rate=Decimal("1.0000"), county_code="7047")])
    assert nuked.rows_written == 1
    assert nuked.table == "tax_rate_period"
    after = store.find_in_force("9000", date(2026, 9, 28), "ST", "GENER")
    assert after.rate == Decimal("1.0000")
    assert len(after.periods) == 1


def test_repeated_key_is_rejected_before_write() -> None:
    store = DynamoTaxRateStore(ensure_local_endpoint())
    store.replace_all([_period(locality_code="1", locality_name="KEEP")])
    try:
        store.replace_all([_period(), _period()])
    except ValueError:
        kept = store.find_in_force("1", date(2026, 9, 28), "ST", "GENER")
        assert kept.locality_code == "1"
        return
    raise AssertionError("expected a repeated key to fail")


def test_missing_table_is_an_error() -> None:
    store = DynamoTaxRateStore(ensure_local_endpoint())
    store._delete_table()
    try:
        store.find_in_force("9000", date(2026, 9, 28), "ST", "GENER")
    except LookupError:
        return
    raise AssertionError("expected a missing table to fail")
