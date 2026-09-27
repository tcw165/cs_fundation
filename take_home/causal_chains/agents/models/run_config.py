from pydantic import BaseModel, Field


class RunConfig(BaseModel):
    include_traces: bool = False
    attempt_quota: int = Field(default=4, ge=1)
