from datetime import datetime
from enum import StrEnum
from typing import Any, ClassVar

from openai.types.responses import EasyInputMessageParam
from pydantic import BaseModel, Field

from take_home.causal_chains.agents.models.messaging.protocol.revision import Revision


class Role(StrEnum):
    user = "user"
    agent = "agent"
    other = "other"
    meta = "meta"


class BaseMessage(BaseModel):
    SCHEMA_VERSION: ClassVar[int] = 1

    message_id: str = Field(..., description="Message id. Part of the sort key.")
    conversation_id: str = Field(..., description="Conversation this message belongs to.")
    user_uuid: str = Field(..., description="Owner of that conversation.")
    role: Role = Field(..., description="Who sent the message.")
    created_timestamp: datetime = Field(
        ...,
        description="When the message was created. The sort key uses this value.",
    )
    transient_id: str | None = Field(
        default=None,
        description="Client id for a send that has not settled. Absent on the stored item when unset.",
    )
    input_guardrail_flagged: bool = Field(
        default=False,
        description="True when an input guardrail tripped on this message. Kept off the client payload.",
    )
    revisions: list[Revision] = Field(
        default_factory=list,
        description="Retractions and text replacements. Empty until one happens.",
    )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BaseMessage):
            return NotImplemented
        return self.message_id == other.message_id

    def __hash__(self) -> int:
        return hash(self.message_id)

    def to_dynamodb(self) -> dict[str, Any]:
        created_at = self.created_timestamp.isoformat()
        item: dict[str, Any] = {
            "PK": f"CONV#{self.conversation_id}",
            "SK": f"MSG#{created_at}#{self.message_id}",
            "user_uuid": self.user_uuid,
            "conversation_id": self.conversation_id,
            "message_id": self.message_id,
            "created_at": created_at,
            "sender": "USER" if self.role is Role.user else "CHATBOT",
            "message_type": self.kind,
            "message_json": self.model_dump(
                mode="json",
                exclude_none=True,
                exclude={"input_guardrail_flagged"},
            ),
            "input_guardrail_flagged": self.input_guardrail_flagged,
            "schema_version": self.SCHEMA_VERSION,
        }
        if self.transient_id is not None:
            item["transient_id"] = self.transient_id
        return item

    def to_openai_message(self) -> EasyInputMessageParam:
        return {
            "type": "message",
            "role": "user" if self.role is Role.user else "assistant",
            "content": self.openai_text(),
        }

    def openai_text(self) -> str:
        raise NotImplementedError
