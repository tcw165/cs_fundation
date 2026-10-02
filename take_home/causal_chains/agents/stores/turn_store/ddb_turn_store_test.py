import asyncio
import time

from take_home.causal_chains.agents.stores.turn_store.ddb_turn_store import DdbTurnStore
from take_home.causal_chains.agents.models.turn.turn import Turn
from take_home.causal_chains.agents.models.turn.turn_status import TurnStatus


class _FakeDynamoDb:
    def __init__(self) -> None:
        self.item: dict[str, object] | None = None

    def put_item(
        self,
        table_name: str,
        item: dict[str, object],
    ) -> None:
        assert table_name == "turn"
        self.item = item

    def get_item(
        self,
        table_name: str,
        key: dict[str, object],
    ) -> dict[str, object] | None:
        if self.item is None:
            return None
        if self.item.get("turn_id") != key["turn_id"]:
            return None
        return self.item

    def query_index(
        self,
        table_name: str,
        index_name: str,
        key_name: str,
        key_value: str,
    ) -> list[dict[str, object]]:
        assert table_name == "turn"
        assert index_name == "conversation_id"
        assert key_name == "conversation_id"
        if self.item is None or self.item.get(key_name) != key_value:
            return []
        return [self.item]

    def delete_item(
        self,
        table_name: str,
        key: dict[str, object],
    ) -> None:
        assert table_name == "turn"
        if self.item is not None and self.item.get("turn_id") == key["turn_id"]:
            self.item = None


def test_put_turn_stores_ttl_about_one_day_ahead():
    async def exercise():
        database = _FakeDynamoDb()
        store = DdbTurnStore(database)
        turn = Turn(
            turn_id="t_1",
            conversation_id="1",
            status=TurnStatus.queued,
            from_message="m_1",
        )
        written_at = time.time()
        await store.put_turn(turn)
        saved = await store.get_turn("t_1")
        return database, written_at, saved, turn

    database, written_at, saved, turn = asyncio.run(exercise())
    assert database.item is not None
    ttl = database.item["ttl"]
    assert isinstance(ttl, int)
    assert abs(ttl - (written_at + 24 * 60 * 60)) < 2
    assert saved == turn


def test_get_turn_by_conversation_reads_the_conversation_index():
    async def exercise():
        database = _FakeDynamoDb()
        store = DdbTurnStore(database)
        turn = Turn(
            turn_id="t_1",
            conversation_id="1",
            status=TurnStatus.queued,
            from_message="m_1",
        )
        await store.put_turn(turn)
        found = await store.get_turn_by_conversation("1")
        missing = await store.get_turn_by_conversation("2")
        return found, missing, turn

    found, missing, turn = asyncio.run(exercise())
    assert found == turn
    assert missing is None


def test_delete_turn_removes_the_item():
    async def exercise():
        database = _FakeDynamoDb()
        store = DdbTurnStore(database)
        turn = Turn(
            turn_id="t_1",
            conversation_id="1",
            status=TurnStatus.running,
            from_message="m_1",
        )
        await store.put_turn(turn)
        await store.delete_turn(turn.turn_id)
        return await store.get_turn(turn.turn_id), await store.get_turn_by_conversation("1")

    saved, by_conversation = asyncio.run(exercise())
    assert saved is None
    assert by_conversation is None
