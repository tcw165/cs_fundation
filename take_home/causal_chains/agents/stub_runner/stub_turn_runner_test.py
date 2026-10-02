import asyncio
from datetime import datetime, timezone

from take_home.causal_chains.agents.agent_runner.protocol.agent_runner import AgentRunner
from take_home.causal_chains.agents.models.messaging.message import MarkdownMessage, Role
from take_home.causal_chains.agents.models.run_clients import RunClients
from take_home.causal_chains.agents.models.run_context import RunContext
from take_home.causal_chains.agents.stub_runner.stub_turn_runner import StubTurnRunner


class _FixedClock:
    def now(self) -> datetime:
        return datetime(2026, 9, 29, 5, 16, tzinfo=timezone.utc)


def test_stub_turn_runner_is_an_agent_runner():
    assert isinstance(StubTurnRunner(), AgentRunner)


def test_stub_turn_runner_stream_yields_one_markdown_message():
    async def collect():
        runner = StubTurnRunner()
        context = RunContext(
            conversation_id="1",
            clock=_FixedClock(),
            turn_id="t_1",
            clients=RunClients(causal_chain_store=object()),
        )
        return [event async for event in await runner.stream(["hello"], context)]

    events = asyncio.run(collect())
    assert len(events) == 1
    message = events[0]
    assert isinstance(message, MarkdownMessage)
    assert message.role is Role.agent
    assert message.text == "echo: hello"
