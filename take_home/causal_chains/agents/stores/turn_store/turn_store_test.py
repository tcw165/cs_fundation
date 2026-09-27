from take_home.causal_chains.agents.stores.turn_store.turn_store import InMemoryTurnStore
from take_home.causal_chains.models.turn import Turn
from take_home.causal_chains.models.turn_status import TurnStatus


def test_in_memory_turn_store_round_trips_a_turn():
    store = InMemoryTurnStore()
    queued = Turn(
        turn_id="t_1",
        conversation_id="1",
        status=TurnStatus.queued,
    )
    store.put_turn(queued)
    assert store.get_turn("t_1") == queued
    completed = queued.model_copy(update={"status": TurnStatus.completed})
    store.put_turn(completed)
    assert store.get_turn("t_1") == completed
    assert store.get_turn("missing") is None
