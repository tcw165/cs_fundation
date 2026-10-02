import asyncio

from take_home.causal_chains.agents.stores.turn_store.protocol.protocol import TurnStore
from take_home.causal_chains.agents.models.turn.turn import Turn
from take_home.causal_chains.agents.models.turn.turn_status import TurnStatus


class _Both:
    def __init__(self) -> None:
        self._turns: dict[str, Turn] = {}

    async def put_turn(
        self,
        turn: Turn,
    ) -> None:
        self._turns[turn.turn_id] = turn

    async def get_turn(
        self,
        turn_id: str,
    ) -> Turn | None:
        return self._turns.get(turn_id)

    async def get_turn_by_conversation(
        self,
        conversation_id: str,
    ) -> Turn | None:
        for turn in self._turns.values():
            if turn.conversation_id == conversation_id:
                return turn
        return None

    async def delete_turn(
        self,
        turn_id: str,
    ) -> None:
        self._turns.pop(turn_id, None)


class _PutOnly:
    async def put_turn(
        self,
        turn: Turn,
    ) -> None:
        return None


def test_turn_store_requires_put_turn_and_get_turn():
    assert isinstance(_Both(), TurnStore)
    assert not isinstance(_PutOnly(), TurnStore)


def test_turn_store_round_trips_a_turn():
    async def exercise():
        store = _Both()
        turn = Turn(
            turn_id="t_1",
            conversation_id="1",
            status=TurnStatus.queued,
            from_message="m_1",
        )
        await store.put_turn(turn)
        saved = await store.get_turn("t_1")
        await store.delete_turn("t_1")
        removed = await store.get_turn("t_1")
        missing = await store.get_turn("missing")
        return saved, removed, missing, turn

    saved, removed, missing, turn = asyncio.run(exercise())
    assert saved == turn
    assert removed is None
    assert missing is None
