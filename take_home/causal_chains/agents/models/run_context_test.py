from take_home.causal_chains.agents.models.run_context import RunContext


def test_run_context_round_trip():
    context = RunContext(conversation_id="1", turn_id="t_1")
    assert context.model_dump() == {"conversation_id": "1", "turn_id": "t_1"}
