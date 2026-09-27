import asyncio

from take_home.causal_chains.agents.agent_runner.protocol.agent_runner import AgentRunner
from take_home.causal_chains.agents.models.runner_context import RunnerContext
from take_home.causal_chains.agents.stub_runner.stub_turn_runner import StubTurnRunner


def test_stub_turn_runner_is_an_agent_runner():
    assert isinstance(StubTurnRunner(), AgentRunner)


def test_stub_turn_runner_stream_yields_delta_then_done():
    async def collect():
        runner = StubTurnRunner()
        context = RunnerContext(conversation_id="1", turn_id="t_1")
        return [event async for event in runner.stream(["hello"], context)]

    events = asyncio.run(collect())
    assert events[0].type == "delta"
    assert events[0].text == "echo: hello"
    assert events[-1].type == "done"
    assert events[-1].message_id == "m_t_1"
