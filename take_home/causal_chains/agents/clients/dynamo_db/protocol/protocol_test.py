from take_home.causal_chains.agents.clients.dynamo_db.protocol.protocol import DynamoDb


class _Both:
    def put_item(self, table_name: str, item: dict[str, object]) -> None:
        return None

    def get_item(self, table_name: str, key: dict[str, object]) -> dict[str, object] | None:
        return None


class _PutOnly:
    def put_item(self, table_name: str, item: dict[str, object]) -> None:
        return None


def test_dynamo_db_requires_put_item_and_get_item():
    assert isinstance(_Both(), DynamoDb)
    assert not isinstance(_PutOnly(), DynamoDb)
