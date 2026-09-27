from take_home.causal_chains.agents.database.turn_store.protocol.protocol import TurnStore
from take_home.causal_chains.models.turn import Turn
from take_home.causal_chains.models.turn_status import TurnStatus


class _Both:
    def __init__(self) -> None:
        self._turns: dict[str, Turn] = {}

    def put_turn(self, turn: Turn) -> None:
        self._turns[turn.turn_id] = turn

    def get_turn(self, turn_id: str) -> Turn | None:
        return self._turns.get(turn_id)


class _PutOnly:
    def put_turn(self, turn: Turn) -> None:
        return None


def test_turn_store_requires_put_turn_and_get_turn():
    assert isinstance(_Both(), TurnStore)
    assert not isinstance(_PutOnly(), TurnStore)


def test_turn_store_round_trips_a_turn():
    store = _Both()
    turn = Turn(
        turn_id="t_1",
        conversation_id="1",
        status=TurnStatus.queued,
    )
    store.put_turn(turn)
    assert store.get_turn("t_1") == turn
    assert store.get_turn("missing") is None
