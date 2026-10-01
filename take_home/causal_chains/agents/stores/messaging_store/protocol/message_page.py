from pydantic import BaseModel, Field

from take_home.causal_chains.agents.models.messaging.message import Message


class MessagePage(BaseModel):
    messages: list[Message] = Field(
        ...,
        description="Messages in this page, oldest first.",
    )
    next_cursor: str | None = Field(
        default=None,
        description="Sort key to pass as start_message for the next page. Absent when this is the last page.",
    )
