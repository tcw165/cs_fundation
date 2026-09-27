from take_home.causal_chains.agents.models.run_clients import RunClients
from take_home.causal_chains.agents.models.run_context import RunContext


def test_run_context_round_trip():
    context = RunContext(
        conversation_id="1",
        turn_id="t_1",
        clients=RunClients(causal_chain_store=object()),
    )
    assert context.model_dump() == {
        "conversation_id": "1",
        "turn_id": "t_1",
        "run_config": {"include_traces": False, "attempt_quota": 4},
    }


def test_clients_stay_off_the_dump():
    store = object()
    clients = RunClients(causal_chain_store=store)
    context = RunContext(conversation_id="1", turn_id="t_1", clients=clients)
    assert context.clients is clients
    assert context.clients.causal_chain_store is store
    assert "clients" not in context.model_dump()
