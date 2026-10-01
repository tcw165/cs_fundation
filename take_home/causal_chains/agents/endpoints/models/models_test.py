import pytest
from pydantic import ValidationError

from take_home.causal_chains.agents.endpoints.models.turn_descriptor import (
    TurnDescriptor,
)
from take_home.causal_chains.agents.endpoints.models.text_input_state import (
    TextInputState,
)
from take_home.causal_chains.agents.endpoints.models.thinking_state import ThinkingState
from take_home.causal_chains.agents.models.messaging.turn.turn import Turn
from take_home.causal_chains.agents.models.messaging.turn.turn_status import TurnStatus
from take_home.causal_chains.agents.endpoints.models.user_interaction_state import (
    DEFAULT_TEXT_INPUT_PLACEHOLDER,
    UserInteractionState,
)


def test_each_text_input_state_value_is_its_name():
    for state in TextInputState:
        assert state.value == state.name


def test_thinking_state_requires_text():
    state = ThinkingState(text="Looking up the chain")
    assert state.text == "Looking up the chain"
    with pytest.raises(ValidationError):
        ThinkingState()


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


def test_turn_descriptor_accepts_empty_lists_and_round_trips():
    empty = TurnDescriptor(processing=[], queued=[])
    assert empty.processing == []
    assert empty.queued == []
    processing = Turn(
        turn_id="t_run",
        conversation_id="1",
        status=TurnStatus.running,
        from_message="m_1",
    )
    queued = Turn(
        turn_id="t_wait",
        conversation_id="1",
        status=TurnStatus.queued,
        from_message="m_2",
    )
    descriptor = TurnDescriptor(processing=[processing], queued=[queued])
    assert TurnDescriptor.model_validate(descriptor.model_dump()) == descriptor
