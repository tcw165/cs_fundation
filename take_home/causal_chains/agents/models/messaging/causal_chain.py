from pydantic import BaseModel, model_validator

from take_home.causal_chains.agents.models.causal_chains.leads_to import LeadsTo
from take_home.causal_chains.agents.models.causal_chains.situation import (
    Situation,
    require_single_root,
)


class CausalChain(BaseModel):
    """One root situation and the situations and links reachable from it."""

    situations: list[Situation]
    links: list[LeadsTo]

    @model_validator(mode="after")
    def one_root(
        self,
    ) -> "CausalChain":
        require_single_root(self.situations)
        return self
