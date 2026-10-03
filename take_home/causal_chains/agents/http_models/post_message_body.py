from pydantic import BaseModel, Field

_TEXT_MAX_LENGTH = 10_000


class PostMessageBody(BaseModel):
    text: str = Field(min_length=1, max_length=_TEXT_MAX_LENGTH - 1)
