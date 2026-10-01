from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class Role(StrEnum):
    user = "user"
    agent = "agent"
    other = "other"
    meta = "meta"


class BaseMessage(BaseModel):
    message_id: str = Field(..., description="Message id.")
    role: Role = Field(..., description="Who sent the message.")
    created_timestamp: datetime = Field(..., description="When the message was created.")
