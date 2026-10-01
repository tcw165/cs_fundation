from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from take_home.causal_chains.agents.endpoints.models.conversation_messages_response import (
    ConversationMessagesResponse,
)
from take_home.causal_chains.agents.endpoints.models.conversation_response import (
    ConversationResponse,
)
from take_home.causal_chains.agents.endpoints.models.turn_descriptor import (
    TurnDescriptor,
)
from take_home.causal_chains.agents.endpoints.models.post_message_response import (
    PostMessageResponse,
)
from take_home.causal_chains.agents.endpoints.models.text_input_state import (
    TextInputState,
)
from take_home.causal_chains.agents.endpoints.models.thinking_state import ThinkingState
from take_home.causal_chains.agents.models.messaging.conversation_status import (
    ConversationStatus,
)
from take_home.causal_chains.agents.models.messaging.message import MarkdownMessage, Role
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


def _markdown() -> MarkdownMessage:
    return MarkdownMessage(
        message_id="m_1",
        conversation_id="1",
        user_uuid="user-1",
        role=Role.agent,
        text="hello",
        created_timestamp=datetime(2026, 9, 30, tzinfo=timezone.utc),
    )


def test_conversation_messages_response_parses_without_a_turn():
    response = ConversationMessagesResponse(
        conversation_id="1",
        messages=[_markdown()],
        user_interaction_state=UserInteractionState(
            text_input_state=TextInputState.ENABLED,
        ),
    )
    assert response.turn is None
    dumped = response.model_dump()
    assert "product" not in dumped
    assert "app" not in dumped
    with_turn = response.model_copy(
        update={"turn": TurnDescriptor(processing=[], queued=[])},
    )
    assert with_turn.turn is not None
    assert with_turn.turn.processing == []


def test_conversation_response_defaults_preview_messages_and_omits_stored_fields():
    response = ConversationResponse(
        id="1",
        status=ConversationStatus.OPEN,
        turn=TurnDescriptor(processing=[], queued=[]),
    )
    assert response.preview_messages == []
    dumped = response.model_dump()
    assert dumped["status"] == ConversationStatus.OPEN
    for stored_field in ("title", "memory", "followup_questions", "entry_context", "active_plan"):
        assert stored_field not in dumped


def test_post_message_response_round_trips_the_message_and_turn():
    message = _markdown()
    turn = Turn(
        turn_id="t_1",
        conversation_id="1",
        status=TurnStatus.queued,
        from_message=message.message_id,
    )
    response = PostMessageResponse(turn=turn, received_message=message)
    assert PostMessageResponse.model_validate(response.model_dump()) == response
