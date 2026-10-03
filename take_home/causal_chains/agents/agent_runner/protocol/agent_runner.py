from typing import Protocol, runtime_checkable

from take_home.causal_chains.agents.agent_runner.protocol.agent_stream import AgentStream
from take_home.causal_chains.agents.models.messaging.message import Message
from take_home.causal_chains.agents.models.run_context import RunContext


@runtime_checkable
class AgentRunner(Protocol):
    async def stream(
        self,
        inputs: list[Message],
        context: RunContext,
    ) -> AgentStream:
        ...
