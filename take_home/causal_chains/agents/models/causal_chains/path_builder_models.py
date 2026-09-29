from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from take_home.causal_chains.agents.models.causal_chains.situation import (
    Situation,
    StartSituation,
    TerminalSituation,
)


class PathBuilderRequest(BaseModel):
    """One step from the current situation toward the saved terminal."""

    model_config = ConfigDict(extra="forbid")

    from_situation: StartSituation | Situation = Field(
        description=(
            "The current situation this step leaves. "
            "The start on the first hop, or the mid-chain situation just linked."
        ),
    )
    terminal_situation: TerminalSituation = Field(
        description=(
            "The saved future this chain is moving toward. Do not create it again."
        ),
    )
    prompt: str = Field(
        description=(
            "The direction for this one step. "
            "It starts with the case id, then the open line from the present "
            "through the current situation including each saved link, "
            "then the one key-factor to change."
        ),
    )

    @model_validator(mode="after")
    def distinct_ends_and_prompt(self) -> Self:
        if not self.prompt.strip():
            raise ValueError("prompt is empty")
        if self.from_situation.situation_id == self.terminal_situation.situation_id:
            raise ValueError("from and terminal are the same situation")
        return self


class PathBuilderResult(BaseModel):
    """Zero or one saved mid-chain situation. Empty means the current situation is already linked to the terminal."""

    model_config = ConfigDict(extra="forbid")

    situation: Situation | None = Field(
        default=None,
        description=(
            "The one saved mid-chain situation, already linked from the current situation, "
            "with one key-factor changed. "
            "None means no new situation was saved, and the current situation "
            "is already linked to the terminal."
        ),
    )

    @model_validator(mode="after")
    def plain_mid_situation(self) -> Self:
        if self.situation is not None and type(self.situation) is not Situation:
            raise ValueError("next situation is mid-chain")
        return self
