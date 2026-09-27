from decimal import Decimal

from pydantic import BaseModel, model_validator

from take_home.causal_chains.agents.models.causal_chain.evidence import Evidence


class LinkInputs(BaseModel):
    """Evidence the pricer supplies. Code turns it into raw_p.

    base_rate is in (0, 1). The agent never writes p. An empty evidence
    list leaves raw_p equal to the base rate.
    """

    base_rate: Decimal
    evidence: list[Evidence] = []

    @model_validator(mode="after")
    def base_rate_is_open_unit_interval(self) -> "LinkInputs":
        if self.base_rate <= 0 or self.base_rate >= 1:
            raise ValueError("base_rate is outside (0, 1)")
        return self
