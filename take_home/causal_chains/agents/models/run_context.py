from pydantic import BaseModel


class RunContext(BaseModel):
    conversation_id: str
    turn_id: str
