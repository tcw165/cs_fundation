from collections.abc import AsyncIterator

from take_home.causal_chains.models.sse_event import SseDelta, SseDone
from take_home.causal_chains.models.turn import Turn
from take_home.causal_chains.protocol.turn_runner import SseEvent


class StubTurnRunner:
    async def run(self, turn: Turn, text: str) -> AsyncIterator[SseEvent]:
        yield SseDelta(text=f"echo: {text}")
        yield SseDone(message_id=f"m_{turn.turn_id}")
