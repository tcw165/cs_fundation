from datetime import date
from decimal import Decimal
from pathlib import Path

from click.testing import CliRunner

from coding.anrok_ai_programming.agent_skills.sales_tax_ingest import ingest
from coding.anrok_ai_programming.models.models import IngestResult, TaxRatePeriod


class _Store:
    def __init__(self, endpoint: str) -> None:
        self.endpoint = endpoint
        self.periods: list[TaxRatePeriod] = []

    def replace_all(self, periods: list[TaxRatePeriod]) -> IngestResult:
        self.periods = periods
        return IngestResult(
            rows_read=len(periods),
            rows_written=len(periods),
            table="tax_rate_period",
            endpoint=self.endpoint,
        )


def test_ingest_nukes_through_replace_all_and_prints_json(tmp_path: Path, monkeypatch) -> None:
    csv_path = tmp_path / "taxrates.csv"
    csv_path.write_text(
        "\n".join(
            [
                "Locality Code,Locality Name,County Number,TaxType,Rate Type,Administered,Active Date,Inactive Date,Rate,Indicator,PJ,County Code,PJ_Rate",
                "7001,AUTAUGA COUNTY,1,ST,GENER,AVENU,20260901,,2.5000,RC,Y,7001,1.2500",
                "7001,AUTAUGA COUNTY,1,ST,GENER,STATE,19791001,19950831,1.0000,NT,,,",
            ]
        )
        + "\n"
    )
    store = _Store("http://127.0.0.1:8002")
    monkeypatch.setattr(ingest, "ensure_local_endpoint", lambda: store.endpoint)
    monkeypatch.setattr(ingest, "DynamoTaxRateStore", lambda endpoint: store)

    result = CliRunner().invoke(ingest.main, ["--csv", str(csv_path)])

    assert result.exit_code == 0
    parsed = IngestResult.model_validate_json(result.output)
    assert parsed.rows_written == 2
    assert parsed.table == "tax_rate_period"
    assert store.periods[0].inactive_date is None
    assert store.periods[0].rate == Decimal("2.5000")
    assert store.periods[1].active_date == date(1979, 10, 1)
    assert store.periods[1].pj is None
    assert store.periods[1].pj_rate is None
