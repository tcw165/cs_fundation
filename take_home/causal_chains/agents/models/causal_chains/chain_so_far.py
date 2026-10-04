from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from take_home.causal_chains.agents.models.causal_chains.leads_to import LeadsTo
from take_home.causal_chains.agents.models.causal_chains.situation import Situation


class LinkedHop(BaseModel):
    """One saved mid-chain situation and the link that reaches it."""

    model_config = ConfigDict(extra="forbid")

    situation: Situation
    link: LeadsTo


class ChainSoFar(BaseModel):
    """The open line from the present through the current situation."""

    model_config = ConfigDict(extra="forbid")

    start: Situation
    hops: list[LinkedHop] = Field(default_factory=list)

    @model_validator(mode="after")
    def hops_follow_the_line(self) -> Self:
        previous = self.start
        for hop in self.hops:
            if hop.situation.kind != "situation":
                raise ValueError("hop situation is mid-chain")
            link = hop.link
            if (
                link.from_situation_id != previous.situation_id
                or link.from_version != previous.version
                or link.to_situation_id != hop.situation.situation_id
                or link.to_version != hop.situation.version
            ):
                raise ValueError("hop does not follow the previous situation")
            previous = hop.situation
        return self
