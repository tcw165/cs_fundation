from typing import Protocol, runtime_checkable

from take_home.causal_chains.models.turn import Turn


@runtime_checkable
class TurnStore(Protocol):
    def put_turn(self, turn: Turn) -> None: ...

    def get_turn(self, turn_id: str) -> Turn | None: ...
