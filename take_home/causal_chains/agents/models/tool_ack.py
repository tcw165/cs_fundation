from pydantic import BaseModel


class ToolAck(BaseModel):
    """Short result from a sub-agent.

    The chain lives on the editor. ok is false when the edit did not finish.
    note is one sentence, not the graph.
    """

    ok: bool
    note: str
