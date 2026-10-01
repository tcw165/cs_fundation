import asyncio
import time

from take_home.causal_chains.agents.stores.turn_store.ddb_turn_store import DdbTurnStore
from take_home.causal_chains.agents.models.messaging.turn.turn import Turn
from take_home.causal_chains.agents.models.messaging.turn.turn_status import TurnStatus


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


def test_put_turn_stores_ttl_about_ten_minutes_ahead():
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
    assert abs(ttl - (written_at + 600)) < 2
    assert saved == turn
