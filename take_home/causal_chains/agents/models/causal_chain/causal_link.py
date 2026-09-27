from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, model_validator

from take_home.causal_chains.agents.models.causal_chain.link_inputs import LinkInputs


class CausalLink(BaseModel):
    """One exclusive next event, plus the inputs that decide its probability.

    raw_p is sigmoid(logit(base_rate) + sum(log_odds)). p is that value
    divided by the sibling raw_p values, and stays unset until every sibling
    has inputs. stale means an ancestor statement changed and p must be recomputed.
    """

    link_id: UUID
    cause_id: UUID
    effect_id: UUID
    inputs: LinkInputs | None = None
    raw_p: Decimal | None = None
    p: Decimal | None = None
    stale: bool = False

    @model_validator(mode="after")
    def reject_self_edge_and_bad_p(self) -> "CausalLink":
        if self.cause_id == self.effect_id:
            raise ValueError("self-edge")
        if self.raw_p is not None and (self.raw_p < 0 or self.raw_p > 1):
            raise ValueError("raw_p is outside 0 to 1")
        if self.p is not None and (self.p < 0 or self.p > 1):
            raise ValueError("p is outside 0 to 1")
        return self
