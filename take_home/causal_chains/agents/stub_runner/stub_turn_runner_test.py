import asyncio

from take_home.causal_chains.agents.stub_runner.stub_turn_runner import StubTurnRunner
from take_home.causal_chains.models.turn import Turn
from take_home.causal_chains.models.turn_status import TurnStatus


def test_stub_turn_runner_yields_delta_then_done():
    async def collect():
        runner = StubTurnRunner()
        turn = Turn(turn_id="t_1", conversation_id="1", status=TurnStatus.queued)
        return [event async for event in runner.run(turn, "hello")]

    events = asyncio.run(collect())
    assert events[0].type == "delta"
    assert events[-1].type == "done"
