from take_home.causal_chains.agents.clients.dynamo_db.boto_dynamo_db import BotoDynamoDb


class _FakeClient:
    def __init__(self) -> None:
        self._items: dict[str, list[dict[str, object]]] = {}

    def put_item(self, **kwargs: object) -> object:
        table_name = str(kwargs["TableName"])
        item = kwargs["Item"]
        assert isinstance(item, dict)
        self._items.setdefault(table_name, []).append(item)
        return {}

    def get_item(self, **kwargs: object) -> dict[str, object]:
        table_name = str(kwargs["TableName"])
        key = kwargs["Key"]
        assert isinstance(key, dict)
        for item in self._items.get(table_name, []):
            if all(item.get(name) == value for name, value in key.items()):
                return {"Item": item}
        return {}

    def query(self, **kwargs: object) -> dict[str, object]:
        table_name = str(kwargs["TableName"])
        values = kwargs["ExpressionAttributeValues"]
        assert isinstance(values, dict)
        expression = str(kwargs["KeyConditionExpression"])
        matched: list[dict[str, object]] = []
        for item in self._items.get(table_name, []):
            if "begins_with" in expression:
                pk_name = expression.split(" = ", 1)[0]
                sk_name = expression.split("begins_with(", 1)[1].split(",", 1)[0]
                prefix = values[":prefix"]
                sk = item.get(sk_name)
                if item.get(pk_name) != values[":pk"]:
                    continue
                if not isinstance(prefix, dict) or not isinstance(sk, dict):
                    continue
                if not str(sk.get("S", "")).startswith(str(prefix.get("S", ""))):
                    continue
                matched.append(item)
                continue
            key_name = expression.split(" = ", 1)[0]
            if item.get(key_name) == values[":value"]:
                matched.append(item)
        return {"Items": matched}


def test_put_item_and_get_item_round_trip_a_string():
    client = _FakeClient()
    database = BotoDynamoDb(client)
    database.put_item("conversation", {"conversation_id": "1"})
    assert database.get_item("conversation", {"conversation_id": "1"}) == {
        "conversation_id": "1",
    }
    assert database.get_item("conversation", {"conversation_id": "missing"}) is None


def test_query_returns_rows_whose_sort_key_has_the_prefix():
    client = _FakeClient()
    database = BotoDynamoDb(client)
    database.put_item("conversation", {"PK": "CONV#1", "SK": "MSG#a"})
    database.put_item("conversation", {"PK": "CONV#1", "SK": "METADATA"})
    database.put_item("conversation", {"PK": "CONV#2", "SK": "MSG#b"})
    rows = database.query("conversation", "PK", "CONV#1", "SK", "MSG#")
    assert rows == [{"PK": "CONV#1", "SK": "MSG#a"}]


def test_query_index_returns_rows_for_the_index_key():
    client = _FakeClient()
    database = BotoDynamoDb(client)
    database.put_item(
        "conversation",
        {"conversation_user_uuid": "user-1", "created_at": "2026-09-30"},
    )
    rows = database.query_index(
        "conversation",
        "conversation_user_uuid",
        "conversation_user_uuid",
        "user-1",
    )
    assert rows == [{"conversation_user_uuid": "user-1", "created_at": "2026-09-30"}]
