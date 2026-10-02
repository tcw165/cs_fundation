from typing import Protocol, runtime_checkable

from take_home.causal_chains.agents.models.turn.turn import Turn


@runtime_checkable
class TurnStore(Protocol):
    async def put_turn(
        self,
        turn: Turn,
    ) -> None: ...

    async def get_turn(
        self,
        turn_id: str,
    ) -> Turn | None: ...

    async def get_turn_by_conversation(
        self,
        conversation_id: str,
    ) -> Turn | None: ...
