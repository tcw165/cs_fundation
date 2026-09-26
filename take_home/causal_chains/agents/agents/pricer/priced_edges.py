from pydantic import BaseModel

from take_home.causal_chains.agents.models.database.leads_to import LeadsTo


class PricedEdges(BaseModel):
    edges: list[LeadsTo]
