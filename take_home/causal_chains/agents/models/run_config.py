from pydantic import BaseModel, Field


class RunConfig(BaseModel):
    """Per-turn limits for one causal chain run."""

    include_traces: bool = False
    causal_chain_max_steps: int = Field(default=20, ge=1)
