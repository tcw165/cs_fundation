from uuid import UUID

from pydantic import BaseModel, Field

from take_home.causal_chains.agents.models.causal_chain.causal_link import CausalLink
from take_home.causal_chains.agents.models.causal_chain.depth_bounds import DepthBounds
from take_home.causal_chains.agents.models.causal_chain.event import Event


class CausalChain(BaseModel):
    """In-memory working set for one hill-climb attempt.

    events and links are keyed by id. root_id stays unset until the editor
    adds the root. This is the object agents read and write. It is not the
    Neo4j row shape.
    """

    events: dict[UUID, Event] = Field(default_factory=dict)
    links: dict[UUID, CausalLink] = Field(default_factory=dict)
    root_id: UUID | None = None
    depth_bounds: DepthBounds = Field(default_factory=DepthBounds)
    max_children: int = 4
