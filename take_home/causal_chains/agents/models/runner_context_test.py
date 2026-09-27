from take_home.causal_chains.agents.models.runner_context import RunnerContext


def test_runner_context_round_trip():
    context = RunnerContext(conversation_id="1", turn_id="t_1")
    assert context.model_dump() == {"conversation_id": "1", "turn_id": "t_1"}
