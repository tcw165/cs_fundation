from typing import override

from take_home.causal_chains.agents.database.turn_store.protocol.protocol import TurnStore
from take_home.causal_chains.models.turn import Turn


class InMemoryTurnStore(TurnStore):
    def __init__(self) -> None:
        self._turns: dict[str, Turn] = {}

    @override
    def put_turn(self, turn: Turn) -> None:
        self._turns[turn.turn_id] = turn

    @override
    def get_turn(self, turn_id: str) -> Turn | None:
        return self._turns.get(turn_id)
