from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, WithJsonSchema, model_validator

_P_SCALE = Decimal("0.0001")
# Pydantic's Decimal schema uses a regex lookahead. OpenAI structured outputs reject it.
_VALUE_SCHEMA = WithJsonSchema(
    {
        "type": "number",
        "minimum": 0,
        "maximum": 1,
    }
)


class InputVariable(BaseModel):
    """A named value between 0 and 1 that a person could move later."""

    name: str
    value: Annotated[Decimal, _VALUE_SCHEMA]

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
