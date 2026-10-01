from take_home.causal_chains.agents.endpoints.models.conversation_response import (
    ConversationResponse,
)
from take_home.causal_chains.agents.endpoints.models.turn_descriptor import (
    TurnDescriptor,
)
from take_home.causal_chains.agents.models.messaging.conversation_status import (
    ConversationStatus,
)


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
