from uuid import UUID

from pydantic import BaseModel

from take_home.causal_chains.agents.models.database.leads_to import LeadsTo
from take_home.causal_chains.agents.models.database.situation import Situation


class ChainGraph(BaseModel):
    situations: list[Situation]
    edges: list[LeadsTo]
    destination_ids: list[UUID]
