from pydantic import BaseModel, Field

from take_home.causal_chains.agents.models.turn.turn import Turn


class TurnDescriptor(BaseModel):
    processing: list[Turn] = Field(
        ...,
        description="Turns running now. Empty when nothing is running.",
    )
    queued: list[Turn] = Field(
        ...,
        description="Turns waiting to run. Empty when nothing is waiting.",
    )
