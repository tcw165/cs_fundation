from enum import StrEnum
from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field, TypeAdapter


class Role(StrEnum):
    user = "user"
    agent = "agent"
    other = "other"
    meta = "meta"


class BaseMessage(BaseModel):
    message_id: str
    role: Role


class MarkdownMessage(BaseMessage):
    type: Literal["markdown"] = "markdown"
    text: str


class HeartbeatMessage(BaseMessage):
    type: Literal["heartbeat"] = "heartbeat"
    role: Literal[Role.meta] = Role.meta


from take_home.causal_chains.agents.models.messaging.message_widgets import (  # noqa: E402
    DeeplinkCardMessage,
)

Message = Annotated[
    Union[MarkdownMessage, DeeplinkCardMessage, HeartbeatMessage],
    Field(discriminator="type"),
]

message_adapter: TypeAdapter[
    MarkdownMessage | DeeplinkCardMessage | HeartbeatMessage
] = TypeAdapter(Message)
