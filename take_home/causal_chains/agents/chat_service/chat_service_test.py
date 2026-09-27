import asyncio

from take_home.causal_chains.agents.chat_service.chat_service import ChatService, format_sse
from take_home.causal_chains.agents.database.messaging_store.messaging_store import (
    InMemoryMessagingStore,
)
from take_home.causal_chains.agents.stub_runner.stub_turn_runner import StubTurnRunner
from take_home.causal_chains.agents.models.messaging.sse_event import RunTraces, SseDelta
from take_home.causal_chains.models.turn_status import TurnStatus


def test_format_sse_excludes_type_from_data():
    line = format_sse(SseDelta(text="oil "))
    assert line.startswith("event: delta\n")
    assert '"type"' not in line.split("data:", 1)[1]
    assert "oil" in line


def test_format_sse_run_traces():
    line = format_sse(RunTraces(text="span\n"))
    assert line.startswith("event: run_traces\n")
    assert "span" in line


def test_post_message_and_subscribe_stub():
    async def exercise():
        store = InMemoryMessagingStore()
        service = ChatService(StubTurnRunner(), store)
        turn = service.post_message("1", "hello")
        assert turn.status is TurnStatus.queued
        events = [event async for event in service.subscribe("1", turn.turn_id)]
        return turn, events, store

    turn, events, store = asyncio.run(exercise())
    assert events[0].type == "delta"
    assert events[-1].type == "done"
    assert turn.conversation_id == "1"
    stored = store.list_messages("1")
    assert len(stored) == 1
    assert stored[0].role == "user"
    assert stored[0].text == "hello"
    assert stored[0].turn_id == turn.turn_id
