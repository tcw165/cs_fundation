import uuid
from collections.abc import AsyncGenerator
from typing import override

from take_home.causal_chains.agents.agent_runner.protocol.agent_runner import AgentRunner
from take_home.causal_chains.agents.models.messaging.message import (
    MarkdownMessage,
    Message,
    Role,
)
from take_home.causal_chains.agents.models.run_context import RunContext


class StubTurnRunner(AgentRunner):
    @override
    async def stream(
        self,
        inputs: list[str],
        context: RunContext,
    ) -> AsyncGenerator[Message]:
        del context
        text = "\n".join(inputs)
        yield MarkdownMessage(
            message_id=str(uuid.uuid4()),
            role=Role.agent,
            text=f"echo: {text}",
        )
