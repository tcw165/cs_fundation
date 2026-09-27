from decimal import Decimal

from pydantic import BaseModel, model_validator

_P_SCALE = Decimal("0.0001")


class InputVariable(BaseModel):
    name: str
    value: Decimal

    @model_validator(mode="after")
    def name_and_value_are_usable(
        self,
    ) -> "InputVariable":
        if not self.name.strip():
            raise ValueError("name is empty")
        if self.value < 0 or self.value > 1:
            raise ValueError("value is outside 0 to 1")
        return self


def probability(
    inputs: list[InputVariable],
) -> Decimal:
    if not inputs:
        raise ValueError("inputs required")
    total = sum((item.value for item in inputs), Decimal("0"))
    return (total / Decimal(len(inputs))).quantize(_P_SCALE)
