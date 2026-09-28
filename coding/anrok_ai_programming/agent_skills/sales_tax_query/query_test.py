from datetime import date
from decimal import Decimal

from click.testing import CliRunner

from coding.anrok_ai_programming.agent_skills.sales_tax_query import query
from coding.anrok_ai_programming.models.models import RetrieveResult, TaxRatePeriod


class _Store:
    def __init__(self, endpoint: str) -> None:
        self.endpoint = endpoint
        self.calls: list[tuple[str, date, str, str]] = []

    def find_in_force(
        self,
        locality: str,
        as_of: date,
        tax_type: str,
        rate_type: str,
    ) -> RetrieveResult:
        self.calls.append((locality, as_of, tax_type, rate_type))
        period = TaxRatePeriod(
            locality_code="9000",
            locality_name="HALEYVILLE",
            county_number="90",
            tax_type=tax_type,
            rate_type=rate_type,
            administered="STATE",
            active_date=date(2026, 1, 1),
            inactive_date=None,
            rate=Decimal("4.0000"),
            indicator="RC",
            pj="Y",
            county_code="7047",
            pj_rate=Decimal("2.0000"),
        )
        other = period.model_copy(update={"county_code": "7067"})
        return RetrieveResult.from_periods(
            locality_code="9000",
            locality_name="HALEYVILLE",
            as_of=as_of,
            tax_type=tax_type,
            rate_type=rate_type,
            periods=[period, other],
        )


def test_query_defaults_to_general_sales_tax_today(monkeypatch) -> None:
    store = _Store("http://127.0.0.1:8002")
    monkeypatch.setattr(query, "ensure_local_endpoint", lambda: store.endpoint)
    monkeypatch.setattr(query, "DynamoTaxRateStore", lambda endpoint: store)

    result = CliRunner().invoke(query.main, ["--locality", "HALEYVILLE"])

    assert result.exit_code == 0
    parsed = RetrieveResult.model_validate_json(result.output)
    assert parsed.rate == Decimal("4.0000")
    assert parsed.rate_unit == "percent"
    assert len(parsed.periods) == 2
    locality, as_of, tax_type, rate_type = store.calls[0]
    assert locality == "HALEYVILLE"
    assert as_of == date.today()
    assert tax_type == "ST"
    assert rate_type == "GENER"


def test_query_accepts_an_as_of_date(monkeypatch) -> None:
    store = _Store("http://127.0.0.1:8002")
    monkeypatch.setattr(query, "ensure_local_endpoint", lambda: store.endpoint)
    monkeypatch.setattr(query, "DynamoTaxRateStore", lambda endpoint: store)

    result = CliRunner().invoke(
        query.main,
        ["--locality", "9000", "--as-of", "2020-01-01", "--tax-type", "CU", "--rate-type", "AUTO"],
    )

    assert result.exit_code == 0
    assert store.calls[0] == ("9000", date(2020, 1, 1), "CU", "AUTO")
