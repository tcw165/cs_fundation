import pytest
from pydantic import ValidationError

from take_home.causal_chains.agents.endpoints.models.thinking_state import ThinkingState


def test_thinking_state_requires_text():
    state = ThinkingState(text="Looking up the chain")
    assert state.text == "Looking up the chain"
    with pytest.raises(ValidationError):
        ThinkingState()
