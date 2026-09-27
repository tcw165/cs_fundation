from typing import Protocol, runtime_checkable


@runtime_checkable
class DynamoDb(Protocol):
    def put_item(self, table_name: str, item: dict[str, object]) -> None: ...

    def get_item(self, table_name: str, key: dict[str, object]) -> dict[str, object] | None: ...
