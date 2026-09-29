from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from take_home.causal_chains.agents.models.causal_chains.case import Case


class NowScoutRequest(BaseModel):
    """The case to save the present on, and the future that present is for."""

    model_config = ConfigDict(extra="forbid")

    case: Case = Field(
        description=(
            "The case just created. Save the start on this case. Do not invent a case id."
        ),
    )
    future: str = Field(
        description=(
            "The hypothetical future. Describe the present this future would leave behind."
        ),
    )

    @model_validator(mode="after")
    def future_present(self) -> Self:
        if not self.future.strip():
            raise ValueError("future is empty")
        return self
