import os
import socket
import subprocess
import time
from datetime import date
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlparse

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from coding.anrok_ai_programming.models.models import IngestResult, RetrieveResult, TaxRatePeriod

TABLE_NAME = "tax_rate_period"
LOCALITY_NAME_INDEX = "locality_name"
DEFAULT_ENDPOINT = "http://127.0.0.1:8002"
_COMPOSE_RUNFILE = "coding/anrok_ai_programming/docker-compose.yml"


class DynamoTaxRateStore:
    def __init__(self, endpoint: str) -> None:
        self._endpoint = endpoint
        self._resource = boto3.resource(
            "dynamodb",
            endpoint_url=endpoint,
            region_name="us-east-1",
            aws_access_key_id="dummy",
            aws_secret_access_key="dummy",
        )
        self._client = self._resource.meta.client

    def replace_all(self, periods: list[TaxRatePeriod]) -> IngestResult:
        _reject_duplicate_keys(periods)
        self._delete_table()
        self._create_table()
        if periods:
            table = self._resource.Table(TABLE_NAME)
            with table.batch_writer() as batch:
                for period in periods:
                    batch.put_item(Item=_item(period))
        return IngestResult(
            rows_read=len(periods),
            rows_written=len(periods),
            table=TABLE_NAME,
            endpoint=self._endpoint,
        )

    def find_in_force(
        self,
        locality: str,
        as_of: date,
        tax_type: str,
        rate_type: str,
    ) -> RetrieveResult:
        try:
            items = self._query(locality, tax_type, rate_type)
        except ClientError as error:
            if error.response.get("Error", {}).get("Code") == "ResourceNotFoundException":
                raise LookupError(f"{TABLE_NAME} is missing") from error
            raise
        periods = [
            period
            for item in items
            if _in_force(period := _period(item), as_of)
        ]
        if periods:
            locality_code = periods[0].locality_code
            locality_name = periods[0].locality_name
        elif locality.isdigit():
            locality_code = locality
            locality_name = ""
        else:
            locality_code = ""
            locality_name = locality
        return RetrieveResult.from_periods(
            locality_code=locality_code,
            locality_name=locality_name,
            as_of=as_of,
            tax_type=tax_type,
            rate_type=rate_type,
            periods=periods,
        )

    def _delete_table(self) -> None:
        try:
            self._client.delete_table(TableName=TABLE_NAME)
        except ClientError as error:
            if error.response.get("Error", {}).get("Code") == "ResourceNotFoundException":
                return
            raise
        self._wait_until_gone()

    def _create_table(self) -> None:
        self._client.create_table(
            TableName=TABLE_NAME,
            AttributeDefinitions=[
                {"AttributeName": "locality_code", "AttributeType": "S"},
                {"AttributeName": "sort_key", "AttributeType": "S"},
                {"AttributeName": "locality_name_key", "AttributeType": "S"},
            ],
            KeySchema=[
                {"AttributeName": "locality_code", "KeyType": "HASH"},
                {"AttributeName": "sort_key", "KeyType": "RANGE"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": LOCALITY_NAME_INDEX,
                    "KeySchema": [
                        {"AttributeName": "locality_name_key", "KeyType": "HASH"},
                        {"AttributeName": "sort_key", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                }
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        self._wait_until_ready()

    def _wait_until_gone(self) -> None:
        for _ in range(40):
            try:
                self._client.describe_table(TableName=TABLE_NAME)
            except ClientError as error:
                if error.response.get("Error", {}).get("Code") == "ResourceNotFoundException":
                    return
                raise
            time.sleep(0.25)
        raise TimeoutError(f"{TABLE_NAME} did not delete")

    def _wait_until_ready(self) -> None:
        for _ in range(40):
            description = self._client.describe_table(TableName=TABLE_NAME)["Table"]
            indexes = description.get("GlobalSecondaryIndexes", [])
            indexes_ready = all(index["IndexStatus"] == "ACTIVE" for index in indexes)
            if description["TableStatus"] == "ACTIVE" and indexes_ready:
                return
            time.sleep(0.25)
        raise TimeoutError(f"{TABLE_NAME} did not become active")

    def _query(self, locality: str, tax_type: str, rate_type: str) -> list[dict[str, object]]:
        table = self._resource.Table(TABLE_NAME)
        prefix = f"{tax_type}#{rate_type}#"
        if locality.isdigit():
            key = Key("locality_code").eq(locality) & Key("sort_key").begins_with(prefix)
            query_args: dict[str, object] = {"KeyConditionExpression": key}
        else:
            key = Key("locality_name_key").eq(locality.upper()) & Key("sort_key").begins_with(prefix)
            query_args = {
                "IndexName": LOCALITY_NAME_INDEX,
                "KeyConditionExpression": key,
            }
        items: list[dict[str, object]] = []
        while True:
            response = table.query(**query_args)
            items.extend(response.get("Items", []))
            last_key = response.get("LastEvaluatedKey")
            if not last_key:
                return items
            query_args["ExclusiveStartKey"] = last_key


def ensure_local_endpoint() -> str:
    endpoint = os.environ.get("DYNAMODB_ENDPOINT_URL", DEFAULT_ENDPOINT)
    if _port_open(endpoint):
        return endpoint
    if endpoint != DEFAULT_ENDPOINT:
        raise RuntimeError(f"dynamodb is not reachable at {endpoint}")
    subprocess.run(
        ["docker", "compose", "-f", str(_compose_file()), "up", "-d", "--wait"],
        check=True,
    )
    if not _port_open(endpoint):
        raise RuntimeError(f"dynamodb local did not open {endpoint}")
    return endpoint


def sort_key(period: TaxRatePeriod) -> str:
    active = period.active_date.strftime("%Y%m%d")
    return (
        f"{period.tax_type}#{period.rate_type}#{active}#"
        f"{period.administered}#{period.county_code}"
    )


def _reject_duplicate_keys(periods: list[TaxRatePeriod]) -> None:
    seen: set[tuple[str, str]] = set()
    for period in periods:
        key = (period.locality_code, sort_key(period))
        if key in seen:
            raise ValueError(f"repeated tax rate key {key[0]} {key[1]}")
        seen.add(key)


def _item(period: TaxRatePeriod) -> dict[str, object]:
    item: dict[str, object] = {
        "locality_code": period.locality_code,
        "sort_key": sort_key(period),
        "locality_name": period.locality_name,
        "locality_name_key": period.locality_name.upper(),
        "county_number": period.county_number,
        "tax_type": period.tax_type,
        "rate_type": period.rate_type,
        "administered": period.administered,
        "active_date": period.active_date.isoformat(),
        "rate": period.rate,
        "indicator": period.indicator,
        "county_code": period.county_code,
    }
    if period.inactive_date is not None:
        item["inactive_date"] = period.inactive_date.isoformat()
    if period.pj is not None:
        item["pj"] = period.pj
    if period.pj_rate is not None:
        item["pj_rate"] = period.pj_rate
    return item


def _period(item: dict[str, object]) -> TaxRatePeriod:
    inactive = item.get("inactive_date")
    pj_rate = item.get("pj_rate")
    return TaxRatePeriod(
        locality_code=str(item["locality_code"]),
        locality_name=str(item["locality_name"]),
        county_number=str(item["county_number"]),
        tax_type=str(item["tax_type"]),
        rate_type=str(item["rate_type"]),
        administered=str(item["administered"]),
        active_date=date.fromisoformat(str(item["active_date"])),
        inactive_date=date.fromisoformat(str(inactive)) if inactive else None,
        rate=Decimal(str(item["rate"])),
        indicator=str(item["indicator"]),
        pj=str(item["pj"]) if item.get("pj") is not None else None,
        county_code=str(item["county_code"]),
        pj_rate=Decimal(str(pj_rate)) if pj_rate is not None else None,
    )


def _in_force(period: TaxRatePeriod, as_of: date) -> bool:
    if period.active_date > as_of:
        return False
    if period.inactive_date is None:
        return True
    return period.inactive_date >= as_of


def _port_open(endpoint: str) -> bool:
    parsed = urlparse(endpoint)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or 80
    with socket.socket() as sock:
        sock.settimeout(0.5)
        return sock.connect_ex((host, port)) == 0


def _compose_file() -> Path:
    workspace = os.environ.get("BUILD_WORKSPACE_DIRECTORY")
    if workspace:
        candidate = Path(workspace) / _COMPOSE_RUNFILE
        if candidate.is_file():
            return candidate
    for root_name in ("RUNFILES_DIR", "TEST_SRCDIR"):
        root = os.environ.get(root_name)
        if not root:
            continue
        workspace_name = os.environ.get("TEST_WORKSPACE", "")
        candidates = [Path(root) / _COMPOSE_RUNFILE]
        if workspace_name:
            candidates.append(Path(root) / workspace_name / _COMPOSE_RUNFILE)
        for candidate in candidates:
            if candidate.is_file():
                return candidate
    raise FileNotFoundError(_COMPOSE_RUNFILE)
