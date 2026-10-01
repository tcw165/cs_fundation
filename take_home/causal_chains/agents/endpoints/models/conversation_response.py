from pydantic import BaseModel, Field

from take_home.causal_chains.agents.endpoints.models.turn_descriptor import TurnDescriptor
from take_home.causal_chains.agents.models.messaging.conversation_status import (
    ConversationStatus,
)
from take_home.causal_chains.agents.models.messaging.message import Message


class ConversationResponse(BaseModel):
    id: str = Field(..., description="Conversation id.")
    status: ConversationStatus = Field(
        ...,
        description="Open, restricted, in progress without messages, in progress with messages, or closed.",
    )
    preview_messages: list[Message] = Field(
        default_factory=list,
        description="Messages shown for this conversation in a list. Empty until there are some.",
    )
    turn: TurnDescriptor = Field(
        ...,
        description="Turns processing and queued. Both lists are empty when nothing is in flight.",
    )
