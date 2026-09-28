from datetime import date, datetime

import click

from coding.anrok_ai_programming.store.dynamo_db.dynamo_db import (
    DynamoTaxRateStore,
    ensure_local_endpoint,
)


@click.command()
@click.option("--locality", required=True)
@click.option("--as-of", default=None)
@click.option("--tax-type", default="ST")
@click.option("--rate-type", default="GENER")
def main(locality: str, as_of: str | None, tax_type: str, rate_type: str) -> None:
    on_date = date.today() if as_of is None else datetime.strptime(as_of, "%Y-%m-%d").date()
    store = DynamoTaxRateStore(ensure_local_endpoint())
    result = store.find_in_force(locality, on_date, tax_type, rate_type)
    click.echo(result.model_dump_json())


if __name__ == "__main__":
    main()
