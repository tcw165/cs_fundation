from datetime import datetime, timezone

from take_home.causal_chains.agents.models.run_clients import RunClients
from take_home.causal_chains.agents.models.run_context import RunContext


class _FixedClock:
    def now(self) -> datetime:
        return datetime(2026, 9, 29, 5, 16, tzinfo=timezone.utc)


def test_run_context_round_trip():
    clock = _FixedClock()
    context = RunContext(
        conversation_id="1",
        clock=clock,
        turn_id="t_1",
        clients=RunClients(causal_chain_store=object()),
    )
    assert context.model_dump() == {
        "conversation_id": "1",
        "turn_id": "t_1",
        "run_config": {"include_traces": False, "causal_chain_max_steps": 50},
    }
    assert context.clock is clock
    assert "clock" not in context.model_dump()


def test_clients_stay_off_the_dump():
    store = object()
    clients = RunClients(causal_chain_store=store)
    context = RunContext(
        conversation_id="1",
        clock=_FixedClock(),
        turn_id="t_1",
        clients=clients,
    )
    assert context.clients is clients
    assert context.clients.causal_chain_store is store
    assert "clients" not in context.model_dump()
