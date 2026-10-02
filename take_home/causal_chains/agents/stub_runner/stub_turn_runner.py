import uuid
from collections.abc import AsyncGenerator, AsyncIterator
from datetime import datetime, timezone
from typing import override

from take_home.causal_chains.agents.agent_runner.protocol.agent_runner import AgentRunner
from take_home.causal_chains.agents.agent_runner.protocol.agent_stream import AgentStream
from take_home.causal_chains.agents.models.messaging.message import (
    MarkdownMessage,
    Message,
    Role,
)
from take_home.causal_chains.agents.models.run_context import RunContext


class _StubStream:
    def __init__(self, inputs: list[str], context: RunContext) -> None:
        self._inputs = inputs
        self._context = context
        self._generator: AsyncGenerator[Message, None] | None = None

    def cancel(self) -> None:
        return

    def __aiter__(self) -> AsyncIterator[Message]:
        self._generator = self._read()
        return self._generator

    async def aclose(self) -> None:
        if self._generator is not None:
            await self._generator.aclose()

    async def _read(self) -> AsyncGenerator[Message, None]:
        text = "\n".join(self._inputs)
        yield MarkdownMessage(
            message_id=str(uuid.uuid4()),
            conversation_id=self._context.conversation_id,
            user_uuid="user-1",
            role=Role.agent,
            text=f"echo: {text}",
            created_timestamp=datetime.now(timezone.utc),
        )


class StubTurnRunner(AgentRunner):
    @override
    async def stream(
        self,
        inputs: list[str],
        context: RunContext,
    ) -> AgentStream:
        return _StubStream(inputs, context)
