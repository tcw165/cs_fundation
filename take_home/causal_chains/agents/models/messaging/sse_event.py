from pydantic import BaseModel


class SseDelta(BaseModel):
    type: str = "delta"
    text: str


class SseTool(BaseModel):
    type: str = "tool"
    name: str
    status: str


class SseDone(BaseModel):
    type: str = "done"
    message_id: str


class SseError(BaseModel):
    type: str = "error"
    message: str


class RunTraces(BaseModel):
    type: str = "run_traces"
    text: str


SseEvent = SseDelta | SseTool | SseDone | SseError | RunTraces
