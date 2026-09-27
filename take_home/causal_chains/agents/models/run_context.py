from pydantic import BaseModel, Field

from take_home.causal_chains.agents.models.run_config import RunConfig


class RunContext(BaseModel):
    conversation_id: str
    turn_id: str
    run_config: RunConfig = Field(default_factory=RunConfig)
