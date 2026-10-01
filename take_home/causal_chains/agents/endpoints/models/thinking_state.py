from pydantic import BaseModel, Field


class ThinkingState(BaseModel):
    text: str = Field(
        ...,
        description="Text to display while the assistant is thinking.",
    )
