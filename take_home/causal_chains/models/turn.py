from pydantic import BaseModel

from take_home.causal_chains.models.turn_status import TurnStatus


class Turn(BaseModel):
    turn_id: str
    conversation_id: str
    status: TurnStatus
