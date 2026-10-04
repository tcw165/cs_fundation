from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

_P_SCALE = Decimal("0.0001")


class InputVariable(BaseModel):
    """One named input on a link. probability is between 0 and 1."""

    name: str = Field(..., description="A short name for this input.")
    desc: str = Field(
        ...,
        description="What this input is, and why this driver could change the situation.",
    )
    probability: float = Field(
        ...,
        ge=0,
        le=1,
        description="A number between 0 and 1 for a driver that could change the situation.",
    )

    @model_validator(mode="after")
    def name_and_desc_are_usable(self) -> "InputVariable":
        if not self.name.strip():
            raise ValueError("name is empty")
        if not self.desc.strip():
            raise ValueError("desc is empty")
        return self


def probability(
    inputs: list[InputVariable],
) -> Decimal:
    if not inputs:
        raise ValueError("inputs required")
    total = sum((Decimal(str(item.probability)) for item in inputs), Decimal("0"))
    return (total / Decimal(len(inputs))).quantize(_P_SCALE)
