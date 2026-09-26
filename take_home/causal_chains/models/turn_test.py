from take_home.causal_chains.models.turn import Turn
from take_home.causal_chains.models.turn_status import TurnStatus


def test_turn_parses_enum_from_string():
    turn = Turn(turn_id="t_8f3a", conversation_id="1", status="queued")
    assert turn.status is TurnStatus.queued
    assert turn.model_dump() == {
        "turn_id": "t_8f3a",
        "conversation_id": "1",
        "status": TurnStatus.queued,
    }
