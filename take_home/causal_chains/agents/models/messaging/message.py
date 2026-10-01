from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field, TypeAdapter

from take_home.causal_chains.agents.models.messaging.message_widgets import (
    DeeplinkCardMessage,
)
from take_home.causal_chains.agents.models.messaging.protocol.message_base import (
    BaseMessage,
    Role,
)


class MarkdownMessage(BaseMessage):
    kind: Literal["markdown"] = Field(default="markdown", description="A markdown chat message.")
    text: str = Field(..., description="The message text.")

    def openai_text(self) -> str:
        return self.text


class HeartbeatMessage(BaseModel):
    """A stream keepalive. It is not stored."""

    kind: Literal["heartbeat"] = Field(
        default="heartbeat",
        description="A stream keepalive. It is not stored.",
    )
    role: Literal[Role.meta] = Field(default=Role.meta, description="Always meta.")


Message = Annotated[
    Union[MarkdownMessage, DeeplinkCardMessage, HeartbeatMessage],
    Field(discriminator="kind"),
]

message_adapter: TypeAdapter[
    MarkdownMessage | DeeplinkCardMessage | HeartbeatMessage
] = TypeAdapter(Message)
