from enum import StrEnum

from pydantic import BaseModel

from take_home.causal_chains.agents.models.causal_chains.situation import Situation


class PathProgress(StrEnum):
    far = "far"
    close = "close"
    closed = "closed"


class DiscoveredSituations(BaseModel):
    situations: list[Situation]
    progress: PathProgress
