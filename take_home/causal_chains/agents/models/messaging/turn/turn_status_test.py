import pytest
from pydantic import ValidationError

from take_home.causal_chains.agents.models.messaging.turn.turn import Turn
from take_home.causal_chains.agents.models.messaging.turn.turn_status import TurnStatus


def test_turn_status_values():
    assert TurnStatus.queued == "queued"
    assert TurnStatus.running == "running"
    assert TurnStatus.completed == "completed"
    assert TurnStatus.failed == "failed"
    assert TurnStatus.cancelled == "cancelled"


def test_turn_status_rejects_unknown():
    with pytest.raises(ValidationError):
        Turn(
            turn_id="t_1",
            conversation_id="1",
            status="unknown",
            from_message="m_1",
        )
