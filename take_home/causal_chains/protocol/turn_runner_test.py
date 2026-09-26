from take_home.causal_chains.models.sse_event import SseDelta
from take_home.causal_chains.models.turn import Turn
from take_home.causal_chains.models.turn_status import TurnStatus
from take_home.causal_chains.protocol.turn_runner import SseEvent


def test_sse_event_union_accepts_delta():
    event: SseEvent = SseDelta(text="hi")
    assert event.type == "delta"
    turn = Turn(turn_id="t_1", conversation_id="1", status=TurnStatus.queued)
    assert turn.turn_id == "t_1"
