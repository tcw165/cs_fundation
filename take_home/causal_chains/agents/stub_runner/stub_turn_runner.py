from collections.abc import AsyncGenerator
from typing import override

from take_home.causal_chains.agents.agent_runner.protocol.agent_runner import AgentRunner
from take_home.causal_chains.agents.models.messaging.sse_event import SseDelta, SseDone, SseEvent
from take_home.causal_chains.agents.models.run_context import RunContext


class StubTurnRunner(AgentRunner):
    @override
    async def stream(
        self,
        inputs: list[str],
        context: RunContext,
    ) -> AsyncGenerator[SseEvent]:
        text = "\n".join(inputs)
        yield SseDelta(text=f"echo: {text}")
        yield SseDone(message_id=f"m_{context.turn_id}")
