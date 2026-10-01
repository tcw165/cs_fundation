from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field


class RevisionRetracted(BaseModel):
    kind: Literal["revision_retracted"] = Field(
        default="revision_retracted",
        description="This revision retracts the message.",
    )
    at: datetime = Field(..., description="When the message was retracted.")


class RevisionUpdated(BaseModel):
    kind: Literal["revision_updated"] = Field(
        default="revision_updated",
        description="This revision replaces the message text.",
    )
    at: datetime = Field(..., description="When the message text was replaced.")
    content: str = Field(..., description="The replacement text.")


Revision = Annotated[
    RevisionRetracted | RevisionUpdated,
    Field(discriminator="kind"),
]
