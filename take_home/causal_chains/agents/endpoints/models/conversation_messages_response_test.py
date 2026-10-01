from datetime import datetime, timezone

from take_home.causal_chains.agents.endpoints.models.conversation_messages_response import (
    ConversationMessagesResponse,
)
from take_home.causal_chains.agents.endpoints.models.text_input_state import (
    TextInputState,
)
from take_home.causal_chains.agents.endpoints.models.turn_descriptor import (
    TurnDescriptor,
)
from take_home.causal_chains.agents.endpoints.models.user_interaction_state import (
    UserInteractionState,
)
from take_home.causal_chains.agents.models.messaging.message import MarkdownMessage, Role


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
