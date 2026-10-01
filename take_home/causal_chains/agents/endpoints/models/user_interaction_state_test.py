from take_home.causal_chains.agents.endpoints.models.text_input_state import (
    TextInputState,
)
from take_home.causal_chains.agents.endpoints.models.thinking_state import ThinkingState
from take_home.causal_chains.agents.endpoints.models.user_interaction_state import (
    DEFAULT_TEXT_INPUT_PLACEHOLDER,
    UserInteractionState,
)


def test_user_interaction_state_defaults_the_placeholder_and_can_carry_thinking():
    state = UserInteractionState(text_input_state=TextInputState.ENABLED)
    assert state.text_input_placeholder == DEFAULT_TEXT_INPUT_PLACEHOLDER
    assert state.thinking_state is None
    thinking = UserInteractionState(
        text_input_state=TextInputState.SEND_ENABLED_WITH_STOP_BUTTON,
        thinking_state=ThinkingState(text="Looking up the chain"),
    )
    assert thinking.thinking_state is not None
    assert thinking.thinking_state.text == "Looking up the chain"
