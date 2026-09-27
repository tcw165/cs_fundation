from pydantic import BaseModel, ConfigDict, Field

from take_home.causal_chains.agents.models.run_clients import RunClients
from take_home.causal_chains.agents.models.run_config import RunConfig


class RunContext(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    conversation_id: str
    turn_id: str
    run_config: RunConfig = Field(default_factory=RunConfig)
    clients: RunClients = Field(exclude=True)
