from take_home.causal_chains.agents.endpoints.models.turn_descriptor import (
    TurnDescriptor,
)
from take_home.causal_chains.agents.models.messaging.turn.turn import Turn
from take_home.causal_chains.agents.models.messaging.turn.turn_status import TurnStatus


def test_turn_descriptor_accepts_empty_lists_and_round_trips():
    empty = TurnDescriptor(processing=[], queued=[])
    assert empty.processing == []
    assert empty.queued == []
    processing = Turn(
        turn_id="t_run",
        conversation_id="1",
        status=TurnStatus.running,
        from_message="m_1",
    )
    queued = Turn(
        turn_id="t_wait",
        conversation_id="1",
        status=TurnStatus.queued,
        from_message="m_2",
    )
    descriptor = TurnDescriptor(processing=[processing], queued=[queued])
    assert TurnDescriptor.model_validate(descriptor.model_dump()) == descriptor
