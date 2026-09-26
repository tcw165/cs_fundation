import asyncio

from take_home.causal_chains.agents.chat_service.chat_service import ChatService, format_sse
from take_home.causal_chains.agents.stub_runner.stub_turn_runner import StubTurnRunner
from take_home.causal_chains.models.sse_event import SseDelta
from take_home.causal_chains.models.turn_status import TurnStatus


def test_format_sse_excludes_type_from_data():
    line = format_sse(SseDelta(text="oil "))
    assert line.startswith("event: delta\n")
    assert '"type"' not in line.split("data:", 1)[1]
    assert "oil" in line


def test_post_message_and_subscribe_stub():
    async def exercise():
        service = ChatService(StubTurnRunner())
        turn = service.post_message("1", "hello")
        assert turn.status is TurnStatus.queued
        events = [event async for event in service.subscribe("1", turn.turn_id)]
        return turn, events

    turn, events = asyncio.run(exercise())
    assert events[0].type == "delta"
    assert events[-1].type == "done"
    assert turn.conversation_id == "1"
