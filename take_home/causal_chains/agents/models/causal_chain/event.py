from uuid import UUID

from pydantic import BaseModel, model_validator


class Event(BaseModel):
    """One hypothesized situation in the chain.

    depth is the hop count from the root. The editor assigns it. is_root is
    true only at depth 0. is_destination marks a dated outcome of the query.
    """

    event_id: UUID
    statement: str
    depth: int
    is_root: bool
    is_destination: bool = False

    @model_validator(mode="after")
    def root_sits_at_depth_zero(self) -> "Event":
        if self.depth < 0:
            raise ValueError("depth is negative")
        if self.is_root and self.depth != 0:
            raise ValueError("root depth is 0")
        return self
