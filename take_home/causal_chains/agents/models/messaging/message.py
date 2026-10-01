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
    type: Literal["markdown"] = "markdown"
    text: str


class HeartbeatMessage(BaseModel):
    """A stream keepalive. It is not stored."""

    type: Literal["heartbeat"] = "heartbeat"
    role: Literal[Role.meta] = Role.meta


Message = Annotated[
    Union[MarkdownMessage, DeeplinkCardMessage, HeartbeatMessage],
    Field(discriminator="type"),
]

message_adapter: TypeAdapter[
    MarkdownMessage | DeeplinkCardMessage | HeartbeatMessage
] = TypeAdapter(Message)
