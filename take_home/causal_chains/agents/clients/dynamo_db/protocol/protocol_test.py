from take_home.causal_chains.agents.clients.dynamo_db.protocol.protocol import DynamoDb


class _Both:
    def put_item(self, table_name: str, item: dict[str, object]) -> None:
        return None

    def get_item(self, table_name: str, key: dict[str, object]) -> dict[str, object] | None:
        return None

    def query(
        self,
        table_name: str,
        key_name: str,
        key_value: str,
        sk_name: str,
        sk_prefix: str,
        limit: int,
        exclusive_start_sk: str | None = None,
    ) -> tuple[list[dict[str, object]], str | None]:
        return [], None

    def query_index(
        self,
        table_name: str,
        index_name: str,
        key_name: str,
        key_value: str,
    ) -> list[dict[str, object]]:
        return []


class _PutOnly:
    def put_item(self, table_name: str, item: dict[str, object]) -> None:
        return None


def test_dynamo_db_requires_put_get_and_query():
    assert isinstance(_Both(), DynamoDb)
    assert not isinstance(_PutOnly(), DynamoDb)
