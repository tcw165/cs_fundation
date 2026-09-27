from collections.abc import AsyncGenerator
from typing import Protocol, runtime_checkable

from take_home.causal_chains.agents.models.messaging.sse_event import SseEvent
from take_home.causal_chains.agents.models.runner_context import RunnerContext


@runtime_checkable
class AgentRunner(Protocol):
    async def stream(
        self,
        inputs: list[str],
        context: RunnerContext,
    ) -> AsyncGenerator[SseEvent]:
        ...
