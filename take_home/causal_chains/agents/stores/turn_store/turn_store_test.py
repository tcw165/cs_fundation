import asyncio

from take_home.causal_chains.agents.stores.turn_store.turn_store import InMemoryTurnStore
from take_home.causal_chains.agents.models.messaging.turn import Turn
from take_home.causal_chains.agents.models.messaging.turn_status import TurnStatus


def test_in_memory_turn_store_round_trips_a_turn():
    async def exercise():
        store = InMemoryTurnStore()
        queued = Turn(
            turn_id="t_1",
            conversation_id="1",
            status=TurnStatus.queued,
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
