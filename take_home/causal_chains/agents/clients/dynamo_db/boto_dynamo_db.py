from typing import Protocol, override

from boto3.dynamodb.types import TypeDeserializer, TypeSerializer

from take_home.causal_chains.agents.clients.dynamo_db.protocol.protocol import DynamoDb


class _LowLevelDynamo(Protocol):
    def put_item(self, **kwargs: object) -> object: ...

    def get_item(self, **kwargs: object) -> dict[str, object]: ...

    def query(self, **kwargs: object) -> dict[str, object]: ...


class BotoDynamoDb(DynamoDb):
    def __init__(self, client: _LowLevelDynamo) -> None:
        self._client = client
        self._serializer = TypeSerializer()
        self._deserializer = TypeDeserializer()

    @override
    def put_item(self, table_name: str, item: dict[str, object]) -> None:
        self._client.put_item(
            TableName=table_name,
            Item={key: self._serializer.serialize(value) for key, value in item.items()},
        )

    @override
    def get_item(self, table_name: str, key: dict[str, object]) -> dict[str, object] | None:
        response = self._client.get_item(
            TableName=table_name,
            Key={name: self._serializer.serialize(value) for name, value in key.items()},
        )
        raw = response.get("Item")
        if raw is None:
            return None
        return {
            name: self._deserializer.deserialize(value)
            for name, value in raw.items()
        }

    def _rows(self, response: dict[str, object]) -> list[dict[str, object]]:
        raw_items = response.get("Items", [])
        if not isinstance(raw_items, list):
            return []
        rows: list[dict[str, object]] = []
        for raw in raw_items:
            if not isinstance(raw, dict):
                continue
            rows.append(
                {
                    name: self._deserializer.deserialize(value)
                    for name, value in raw.items()
                }
            )
        return rows

    @override
    def query(
        self,
        table_name: str,
        key_name: str,
        key_value: str,
        sk_name: str,
        sk_prefix: str,
    ) -> list[dict[str, object]]:
        response = self._client.query(
            TableName=table_name,
            KeyConditionExpression=f"{key_name} = :pk AND begins_with({sk_name}, :prefix)",
            ExpressionAttributeValues={
                ":pk": self._serializer.serialize(key_value),
                ":prefix": self._serializer.serialize(sk_prefix),
            },
        )
        return self._rows(response)

    @override
    def query_index(
        self,
        table_name: str,
        index_name: str,
        key_name: str,
        key_value: str,
    ) -> list[dict[str, object]]:
        response = self._client.query(
            TableName=table_name,
            IndexName=index_name,
            KeyConditionExpression=f"{key_name} = :value",
            ExpressionAttributeValues={
                ":value": self._serializer.serialize(key_value),
            },
        )
        return self._rows(response)
