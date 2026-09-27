from pydantic import BaseModel

from take_home.causal_chains.agents.models.causal_chains.input_variable import (
    InputVariable,
)


class LinkInputs(BaseModel):
    """Input variables for one leads-to link. The link tool computes the probability."""

    inputs: list[InputVariable]
