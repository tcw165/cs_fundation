from pydantic import BaseModel, Field

from take_home.causal_chains.agents.endpoints.models.turn_descriptor import TurnDescriptor
from take_home.causal_chains.agents.endpoints.models.user_interaction_state import (
    UserInteractionState,
)
from take_home.causal_chains.agents.models.messaging.message import Message


class ConversationMessagesResponse(BaseModel):
    conversation_id: str = Field(..., min_length=1, description="Id of the conversation.")
    messages: list[Message] = Field(..., description="Messages in the conversation.")
    user_interaction_state: UserInteractionState = Field(
        ...,
        description="What the reader can do right now.",
    )
    turn: TurnDescriptor | None = Field(
        default=None,
        description="Turns processing and queued. Absent when none are in flight.",
    )
