from collections.abc import AsyncIterator
from typing import Protocol

from take_home.causal_chains.agents.models.messaging.sse_event import SseEvent
from take_home.causal_chains.models.turn import Turn


class TurnRunner(Protocol):
    def run(self, turn: Turn, text: str) -> AsyncIterator[SseEvent]:
        ...
