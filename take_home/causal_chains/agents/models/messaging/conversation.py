from datetime import datetime
from typing import Any, ClassVar

from openai.types.responses import EasyInputMessageParam
from pydantic import BaseModel, Field

from take_home.causal_chains.agents.models.messaging.conversation_status import (
    ConversationStatus,
)
from take_home.causal_chains.agents.models.messaging.entry_context import EntryContext
from take_home.causal_chains.agents.models.messaging.followup_question import (
    FollowupQuestion,
)
from take_home.causal_chains.agents.models.messaging.plan.plan import Plan


class Conversation(BaseModel):
    SCHEMA_VERSION: ClassVar[int] = 1

    id: str = Field(..., description="Conversation id. The table key uses this value.")
    user_uuid: str = Field(..., description="Owner. Also the sparse index key.")
    title: str = Field(..., description="Short name of the conversation.")
    status: ConversationStatus = Field(
        ...,
        description="Open, restricted, in progress without messages, in progress with messages, or closed.",
    )
    followup_questions: list[FollowupQuestion] = Field(
        default_factory=list,
        description="Questions to offer after the latest reply. Empty when there are none.",
    )
    generation_started_at: datetime | None = Field(
        default=None,
        description="When the current reply started. Absent when nothing is generating.",
    )
    entry_context: EntryContext = Field(
        ...,
        description="How the reader opened the conversation. A MyBlog value carries the source URL and IP.",
    )
    memory: str | None = Field(
        default=None,
        max_length=4096,
        description="Notes kept for later turns. Absent when there are none. At most 4096 characters.",
    )
    active_plan: Plan | None = Field(
        default=None,
        description="Plan the conversation is carrying out. Absent when there is no plan.",
    )
    created_at: datetime = Field(..., description="When the conversation was created.")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Conversation):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    def to_dynamodb(self) -> dict[str, Any]:
        return {
            "PK": f"CONV#{self.id}",
            "SK": "METADATA",
            "user_uuid": self.user_uuid,
            "conversation_user_uuid": self.user_uuid,
            "conversation_id": self.id,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "schema_version": self.SCHEMA_VERSION,
            "conversation_json": self.model_dump(mode="json"),
        }

    @classmethod
    def from_dynamodb(cls, item: dict[str, Any]) -> "Conversation":
        return cls.model_validate(item["conversation_json"])

    def to_openai_message(self) -> EasyInputMessageParam:
        parts = [self.title]
        if self.memory is not None:
            parts.append(self.memory)
        return {"type": "message", "role": "system", "content": "\n".join(parts)}
