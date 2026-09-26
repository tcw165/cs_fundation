from pydantic import BaseModel


class PostMessageBody(BaseModel):
    text: str
