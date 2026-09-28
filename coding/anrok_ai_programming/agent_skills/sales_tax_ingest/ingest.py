import csv
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import click

from coding.anrok_ai_programming.models.models import TaxRatePeriod
from coding.anrok_ai_programming.store.dynamo_db.dynamo_db import (
    DynamoTaxRateStore,
    ensure_local_endpoint,
)


@click.command()
@click.option("--csv", required=True, type=click.Path(exists=True, dir_okay=False))
def main(csv: str) -> None:
    periods = read_periods(Path(csv))
    store = DynamoTaxRateStore(ensure_local_endpoint())
    result = store.replace_all(periods)
    click.echo(result.model_dump_json())


def read_periods(path: Path) -> list[TaxRatePeriod]:
    with path.open(newline="") as handle:
        return [_period(row) for row in csv.DictReader(handle)]


def _period(row: dict[str, str]) -> TaxRatePeriod:
    inactive = row["Inactive Date"].strip()
    pj = row["PJ"].strip()
    pj_rate = row["PJ_Rate"].strip()
    return TaxRatePeriod(
        locality_code=row["Locality Code"].strip(),
        locality_name=row["Locality Name"].strip(),
        county_number=row["County Number"].strip(),
        tax_type=row["TaxType"].strip(),
        rate_type=row["Rate Type"].strip(),
        administered=row["Administered"].strip(),
        active_date=_date(row["Active Date"]),
        inactive_date=_date(inactive) if inactive else None,
        rate=Decimal(row["Rate"].strip()),
        indicator=row["Indicator"].strip(),
        pj=pj or None,
        county_code=row["County Code"].strip(),
        pj_rate=Decimal(pj_rate) if pj_rate else None,
    )


def _date(value: str) -> date:
    return datetime.strptime(value.strip(), "%Y%m%d").date()


if __name__ == "__main__":
    main()
