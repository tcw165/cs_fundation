import asyncio

from take_home.causal_chains.agents.stores.turn_store.in_mem_turn_store import InMemoryTurnStore
from take_home.causal_chains.agents.models.turn.turn import Turn
from take_home.causal_chains.agents.models.turn.turn_status import TurnStatus


def test_in_memory_turn_store_round_trips_a_turn():
    async def exercise():
        store = InMemoryTurnStore()
        queued = Turn(
            turn_id="t_1",
            conversation_id="1",
            status=TurnStatus.queued,
            from_message="m_1",
        )
        await store.put_turn(queued)
        first = await store.get_turn("t_1")
        completed = queued.model_copy(update={"status": TurnStatus.completed})
        await store.put_turn(completed)
        second = await store.get_turn("t_1")
        missing = await store.get_turn("missing")
        return first, second, missing, queued, completed

    first, second, missing, queued, completed = asyncio.run(exercise())
    assert first == queued
    assert second == completed
    assert missing is None


def test_in_memory_turn_store_finds_a_turn_by_conversation():
    async def exercise():
        store = InMemoryTurnStore()
        first = Turn(
            turn_id="t_1",
            conversation_id="1",
            status=TurnStatus.queued,
            from_message="m_1",
        )
        other = Turn(
            turn_id="t_2",
            conversation_id="2",
            status=TurnStatus.queued,
            from_message="m_2",
        )
        await store.put_turn(first)
        await store.put_turn(other)
        found = await store.get_turn_by_conversation("1")
        missing = await store.get_turn_by_conversation("missing")
        return found, missing, first

    found, missing, first = asyncio.run(exercise())
    assert found == first
    assert missing is None


def test_in_memory_turn_store_prefers_an_open_turn():
    async def exercise():
        store = InMemoryTurnStore()
        finished = Turn(
            turn_id="t_done",
            conversation_id="1",
            status=TurnStatus.completed,
            from_message="m_1",
        )
        running = Turn(
            turn_id="t_open",
            conversation_id="1",
            status=TurnStatus.running,
            from_message="m_2",
        )
        await store.put_turn(finished)
        await store.put_turn(running)
        return await store.get_turn_by_conversation("1")

    found = asyncio.run(exercise())
    assert found is not None
    assert found.turn_id == "t_open"


def test_in_memory_turn_store_deletes_a_turn():
    async def exercise():
        store = InMemoryTurnStore()
        turn = Turn(
            turn_id="t_1",
            conversation_id="1",
            status=TurnStatus.running,
            from_message="m_1",
        )
        await store.put_turn(turn)
        await store.delete_turn(turn.turn_id)
        return await store.get_turn(turn.turn_id), await store.get_turn_by_conversation("1")

    saved, by_conversation = asyncio.run(exercise())
    assert saved is None
    assert by_conversation is None
