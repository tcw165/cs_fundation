from take_home.causal_chains.agents.clients.dynamo_db.boto_dynamo_db import BotoDynamoDb


class _FakeClient:
    def __init__(self) -> None:
        self._items: dict[str, dict[str, object]] = {}

    def put_item(self, **kwargs: object) -> object:
        table_name = str(kwargs["TableName"])
        item = kwargs["Item"]
        assert isinstance(item, dict)
        self._items[table_name] = item
        return {}

    def get_item(self, **kwargs: object) -> dict[str, object]:
        table_name = str(kwargs["TableName"])
        key = kwargs["Key"]
        assert isinstance(key, dict)
        item = self._items.get(table_name)
        if item is None:
            return {}
        for name, value in key.items():
            if item.get(name) != value:
                return {}
        return {"Item": item}


def test_put_item_and_get_item_round_trip_a_string():
    client = _FakeClient()
    database = BotoDynamoDb(client)
    database.put_item("conversation", {"conversation_id": "1"})
    assert database.get_item("conversation", {"conversation_id": "1"}) == {
        "conversation_id": "1",
    }
    assert database.get_item("conversation", {"conversation_id": "missing"}) is None
