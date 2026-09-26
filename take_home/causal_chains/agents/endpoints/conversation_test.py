import asyncio

from take_home.causal_chains.agents.chat_service.chat_service import ChatService
from take_home.causal_chains.agents.stub_runner.stub_turn_runner import StubTurnRunner
from take_home.causal_chains.models.turn_status import TurnStatus


def test_chat_service_post_returns_queued_turn():
    async def exercise():
        service = ChatService(StubTurnRunner())
        turn = service.post_message("1", "hello")
        assert turn.status is TurnStatus.queued
        events = [event async for event in service.subscribe("1", turn.turn_id)]
        return events

    events = asyncio.run(exercise())
    assert any(event.type == "delta" for event in events)
    assert events[-1].type == "done"
