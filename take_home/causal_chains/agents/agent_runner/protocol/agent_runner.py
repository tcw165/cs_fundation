from collections.abc import AsyncGenerator
from typing import Protocol, runtime_checkable

from take_home.causal_chains.agents.models.messaging.sse_event import SseEvent
from take_home.causal_chains.agents.models.run_context import RunContext


@runtime_checkable
class AgentRunner(Protocol):
    async def stream(
        self,
        inputs: list[str],
        context: RunContext,
    ) -> AsyncGenerator[SseEvent]:
        ...
