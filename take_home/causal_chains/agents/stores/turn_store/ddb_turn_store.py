import time
from typing import override

from take_home.causal_chains.agents.clients.dynamo_db.protocol.protocol import DynamoDb
from take_home.causal_chains.agents.stores.turn_store.protocol.protocol import TurnStore
from take_home.causal_chains.agents.models.turn.turn import Turn

_TURN_TTL_SECONDS = 600


class DdbTurnStore(TurnStore):
    def __init__(
        self,
        dynamo_db: DynamoDb,
    ) -> None:
        self._dynamo_db = dynamo_db

    @override
    async def put_turn(
        self,
        turn: Turn,
    ) -> None:
        item = turn.model_dump()
        item["ttl"] = int(time.time()) + _TURN_TTL_SECONDS
        self._dynamo_db.put_item("turn", item)

    @override
    async def get_turn(
        self,
        turn_id: str,
    ) -> Turn | None:
        item = self._dynamo_db.get_item("turn", {"turn_id": turn_id})
        if item is None:
            return None
        return Turn.model_validate(item)

    @override
    async def get_turn_by_conversation(
        self,
        conversation_id: str,
    ) -> Turn | None:
        rows = self._dynamo_db.query_index(
            "turn",
            "conversation_id",
            "conversation_id",
            conversation_id,
        )
        if len(rows) == 0:
            return None
        return Turn.model_validate(rows[0])

    @override
    async def delete_turn(
        self,
        turn_id: str,
    ) -> None:
        self._dynamo_db.delete_item("turn", {"turn_id": turn_id})
