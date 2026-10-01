from typing import Annotated, Literal

from pydantic import BaseModel, Field


class TextFollowupQuestion(BaseModel):
    kind: Literal["text_followup_question"] = Field(
        default="text_followup_question",
        description="Text question, with no link.",
    )
    content: str = Field(..., description="The question shown to the reader.")


class UriFollowupQuestion(BaseModel):
    kind: Literal["uri_followup_question"] = Field(
        default="uri_followup_question",
        description="Question that opens a link.",
    )
    preview: str = Field(..., description="Short text shown for the link.")
    source_uri: str = Field(..., description="Link this question opens.")


FollowupQuestion = Annotated[
    TextFollowupQuestion | UriFollowupQuestion,
    Field(discriminator="kind"),
]
