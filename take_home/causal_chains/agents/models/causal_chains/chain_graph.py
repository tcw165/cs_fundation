from uuid import UUID

from pydantic import BaseModel

from take_home.causal_chains.agents.models.causal_chains.leads_to import LeadsTo
from take_home.causal_chains.agents.models.causal_chains.situation import Situation


class ChainGraph(BaseModel):
    situations: list[Situation]
    edges: list[LeadsTo]
    destination_ids: list[UUID]
