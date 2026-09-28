from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from take_home.causal_chains.agents.models.causal_chains.input_variable import (
    InputVariable,
    probability,
)


class LeadsTo(BaseModel):
    """A stored link. p is the probability of inputs when inputs are present."""

    from_situation_id: UUID
    from_version: int
    to_situation_id: UUID
    to_version: int
    p: Decimal
    inputs: list[InputVariable] = Field(default_factory=list)

    @model_validator(mode="after")
    def reject_self_edge_and_bad_p(self) -> "LeadsTo":
        if self.from_situation_id == self.to_situation_id:
            raise ValueError("self-edge")
        if self.p < 0 or self.p > 1:
            raise ValueError("p is outside 0 to 1")
        if self.inputs and self.p != probability(self.inputs):
            raise ValueError("p is not the probability of the inputs")
        return self
