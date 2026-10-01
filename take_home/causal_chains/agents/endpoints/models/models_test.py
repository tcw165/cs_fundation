from take_home.causal_chains.agents.endpoints.models.text_input_state import (
    TextInputState,
)


def test_each_text_input_state_value_is_its_name():
    for state in TextInputState:
        assert state.value == state.name
