import pytest
from pydantic import ValidationError

from take_home.causal_chains.agents.endpoints.models.text_input_state import (
    TextInputState,
)
from take_home.causal_chains.agents.endpoints.models.thinking_state import ThinkingState


def test_each_text_input_state_value_is_its_name():
    for state in TextInputState:
        assert state.value == state.name


def test_thinking_state_requires_text():
    state = ThinkingState(text="Looking up the chain")
    assert state.text == "Looking up the chain"
    with pytest.raises(ValidationError):
        ThinkingState()
