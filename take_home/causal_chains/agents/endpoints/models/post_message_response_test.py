from datetime import datetime, timezone

from take_home.causal_chains.agents.endpoints.models.post_message_response import (
    PostMessageResponse,
)
from take_home.causal_chains.agents.models.messaging.message import MarkdownMessage, Role
from take_home.causal_chains.agents.models.messaging.turn.turn import Turn
from take_home.causal_chains.agents.models.messaging.turn.turn_status import TurnStatus


def _markdown() -> MarkdownMessage:
    return MarkdownMessage(
        message_id="m_1",
        conversation_id="1",
        user_uuid="user-1",
        role=Role.agent,
        text="hello",
        created_timestamp=datetime(2026, 9, 30, tzinfo=timezone.utc),
    )


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
