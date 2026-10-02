from typing import override

from take_home.causal_chains.agents.stores.turn_store.protocol.protocol import TurnStore
from take_home.causal_chains.agents.models.messaging.turn.turn import Turn


class InMemoryTurnStore(TurnStore):
    def __init__(self) -> None:
        self._turns: dict[str, Turn] = {}

    @override
    async def put_turn(
        self,
        turn: Turn,
    ) -> None:
        self._turns[turn.turn_id] = turn

    @override
    async def get_turn(
        self,
        turn_id: str,
    ) -> Turn | None:
        return self._turns.get(turn_id)

    @override
    async def get_turn_by_conversation(
        self,
        conversation_id: str,
    ) -> Turn | None:
        for turn in self._turns.values():
            if turn.conversation_id == conversation_id:
                return turn
        return None
