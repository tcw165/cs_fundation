from collections.abc import AsyncIterator

from take_home.causal_chains.agents.models.messaging.sse_event import SseDelta, SseDone, SseEvent
from take_home.causal_chains.models.turn import Turn


class StubTurnRunner:
    async def run(self, turn: Turn, text: str) -> AsyncIterator[SseEvent]:
        yield SseDelta(text=f"echo: {text}")
        yield SseDone(message_id=f"m_{turn.turn_id}")
