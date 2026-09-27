import asyncio

from take_home.causal_chains.agents.chat_service.chat_service import ChatService
from take_home.causal_chains.agents.database.messaging_store.messaging_store import (
    InMemoryMessagingStore,
)
from take_home.causal_chains.agents.database.turn_store.turn_store import InMemoryTurnStore
from take_home.causal_chains.agents.stub_runner.stub_turn_runner import StubTurnRunner
from take_home.causal_chains.models.turn_status import TurnStatus


def test_chat_service_post_returns_queued_turn():
    async def exercise():
        store = InMemoryMessagingStore()
        turn_store = InMemoryTurnStore()
        service = ChatService(StubTurnRunner(), store, turn_store)
        turn = service.post_message("1", "hello")
        assert turn.status is TurnStatus.queued
        await service.run_turn(turn, "hello")
        events = [event async for event in service.subscribe("1", turn.turn_id)]
        return turn, events, store, turn_store

    turn, events, store, turn_store = asyncio.run(exercise())
    assert any(event.type == "delta" for event in events)
    assert events[-1].type == "done"
    stored = store.list_messages("1")
    assert len(stored) == 1
    assert stored[0].text == "hello"
    saved = turn_store.get_turn(turn.turn_id)
    assert saved is not None
    assert saved.status is TurnStatus.completed
