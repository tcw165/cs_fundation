from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, model_validator


class LeadsTo(BaseModel):
    from_situation_id: UUID
    to_situation_id: UUID
    p: Decimal

    @model_validator(mode="after")
    def reject_self_edge_and_bad_p(self) -> "LeadsTo":
        if self.from_situation_id == self.to_situation_id:
            raise ValueError("self-edge")
        if self.p < 0 or self.p > 1:
            raise ValueError("p is outside 0 to 1")
        return self
