from pydantic import BaseModel, Field


class RunConfig(BaseModel):
    """Per-turn limits for one causal chain run."""

    include_traces: bool = False
    attempt_quota: int = Field(default=20, ge=1)
