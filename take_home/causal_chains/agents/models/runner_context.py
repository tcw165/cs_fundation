from pydantic import BaseModel


class RunnerContext(BaseModel):
    conversation_id: str
    turn_id: str
