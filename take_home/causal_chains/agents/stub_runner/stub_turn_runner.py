from collections.abc import AsyncGenerator, AsyncIterator

from take_home.causal_chains.agents.models.messaging.sse_event import SseDelta, SseDone, SseEvent
from take_home.causal_chains.agents.models.runner_context import RunnerContext
from take_home.causal_chains.models.turn import Turn


class StubTurnRunner:
    async def stream(
        self,
        inputs: list[str],
        context: RunnerContext,
    ) -> AsyncGenerator[SseEvent]:
        text = "\n".join(inputs)
        yield SseDelta(text=f"echo: {text}")
        yield SseDone(message_id=f"m_{context.turn_id}")

    async def run(self, turn: Turn, text: str) -> AsyncIterator[SseEvent]:
        context = RunnerContext(
            conversation_id=turn.conversation_id,
            turn_id=turn.turn_id,
        )
        async for event in self.stream([text], context):
            yield event
