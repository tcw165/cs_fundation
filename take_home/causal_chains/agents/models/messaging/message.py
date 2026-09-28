from pydantic import BaseModel


class Message(BaseModel):
    message_id: str
    conversation_id: str
    turn_id: str | None
    role: str
    text: str
