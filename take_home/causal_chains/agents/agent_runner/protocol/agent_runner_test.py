from take_home.causal_chains.agents.models.messaging.sse_event import SseDelta, SseEvent
from take_home.causal_chains.agents.models.runner_context import RunnerContext


def test_agent_runner_event_and_context():
    event: SseEvent = SseDelta(text="hi")
    assert event.type == "delta"
    context = RunnerContext(conversation_id="1", turn_id="t_1")
    assert context.turn_id == "t_1"
