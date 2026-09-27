from take_home.causal_chains.agents.models.messaging.sse_event import SseDelta, SseEvent
from take_home.causal_chains.models.turn import Turn
from take_home.causal_chains.models.turn_status import TurnStatus


def test_sse_event_union_accepts_delta():
    event: SseEvent = SseDelta(text="hi")
    assert event.type == "delta"
    turn = Turn(turn_id="t_1", conversation_id="1", status=TurnStatus.queued)
    assert turn.turn_id == "t_1"
