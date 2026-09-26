from pydantic import BaseModel


class Conversation(BaseModel):
    conversation_id: str
