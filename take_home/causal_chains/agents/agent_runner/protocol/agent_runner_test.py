from take_home.causal_chains.agents.agent_runner.protocol.agent_runner import AgentRunner
from take_home.causal_chains.agents.models.messaging.sse_event import SseDelta, SseEvent
from take_home.causal_chains.agents.models.runner_context import RunnerContext


class _WithStream:
    async def stream(self, inputs: list[str], context: RunnerContext):
        if False:
            yield SseDelta(text="")


class _WithoutStream:
    pass


def test_agent_runner_is_runtime_checkable():
    assert isinstance(_WithStream(), AgentRunner)
    assert not isinstance(_WithoutStream(), AgentRunner)


def test_agent_runner_event_and_context():
    event: SseEvent = SseDelta(text="hi")
    assert event.type == "delta"
    context = RunnerContext(conversation_id="1", turn_id="t_1")
    assert context.turn_id == "t_1"
