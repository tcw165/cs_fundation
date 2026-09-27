from pydantic import BaseModel

from take_home.causal_chains.agents.models.causal_chains.leads_to import LeadsTo


class PricedEdges(BaseModel):
    edges: list[LeadsTo]
