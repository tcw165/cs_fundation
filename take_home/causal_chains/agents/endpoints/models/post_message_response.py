from pydantic import BaseModel, Field

from take_home.causal_chains.agents.models.messaging.message import Message
from take_home.causal_chains.agents.models.turn.turn import Turn


class PostMessageResponse(BaseModel):
    turn: Turn = Field(..., description="The turn queued for this send.")
    received_message: Message = Field(
        ...,
        description="The message that was stored for this send.",
    )
