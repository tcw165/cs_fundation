from uuid import UUID

from pydantic import BaseModel

from take_home.causal_chains.agents.models.causal_chains.situation import Situation


class UnpricedEdge(BaseModel):
    from_situation_id: UUID
    to_situation_id: UUID


class UnpricedChain(BaseModel):
    situations: list[Situation]
    edges: list[UnpricedEdge]
    destination_ids: list[UUID]
