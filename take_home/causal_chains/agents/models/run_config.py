from pydantic import BaseModel


class RunConfig(BaseModel):
    include_traces: bool = False
