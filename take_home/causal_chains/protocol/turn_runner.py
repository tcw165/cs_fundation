from collections.abc import AsyncIterator
from typing import Protocol

from take_home.causal_chains.models.sse_event import SseDelta, SseDone, SseError, SseTool
from take_home.causal_chains.models.turn import Turn

SseEvent = SseDelta | SseTool | SseDone | SseError


class TurnRunner(Protocol):
    def run(self, turn: Turn, text: str) -> AsyncIterator[SseEvent]:
        ...
