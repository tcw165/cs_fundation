from typing import Protocol, runtime_checkable


@runtime_checkable
class DynamoDb(Protocol):
    def put_item(self, table_name: str, item: dict[str, object]) -> None: ...

    def get_item(self, table_name: str, key: dict[str, object]) -> dict[str, object] | None: ...

    def query(
        self,
        table_name: str,
        key_name: str,
        key_value: str,
        sk_name: str,
        sk_prefix: str,
    ) -> list[dict[str, object]]: ...

    def query_index(
        self,
        table_name: str,
        index_name: str,
        key_name: str,
        key_value: str,
    ) -> list[dict[str, object]]: ...
