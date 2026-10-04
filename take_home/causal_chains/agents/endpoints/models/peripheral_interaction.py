from typing import Annotated, Literal

from pydantic import BaseModel, Field


class CausalChainCase(BaseModel):
    kind: Literal["causal_chain_case"] = "causal_chain_case"
    case_id: str = Field(..., description="The case this interaction points at.")
    from_message_id: str = Field(..., description="The message that created this case.")


class LinkedConversation(BaseModel):
    kind: Literal["linked_conversation"] = "linked_conversation"
    conversation_id: str = Field(
        ...,
        description="The conversation this interaction points at.",
    )


PeripheralInteraction = Annotated[
    CausalChainCase | LinkedConversation,
    Field(discriminator="kind"),
]
