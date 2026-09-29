from uuid import UUID

from pydantic import BaseModel, model_validator

from take_home.causal_chains.agents.models.causal_chains.leads_to import LeadsTo
from take_home.causal_chains.agents.models.causal_chains.situation import (
    Situation,
    StartSituation,
    TerminalSituation,
    require_single_start,
)


class CausalChain(BaseModel):
    """One start situation and the situations and links reachable from it."""

    situations: list[StartSituation | TerminalSituation | Situation]
    links: list[LeadsTo]
    case_id: UUID | None = None

    @model_validator(mode="after")
    def one_start(
        self,
    ) -> "CausalChain":
        require_single_start(self.situations)
        return self
