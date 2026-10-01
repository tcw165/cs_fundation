from datetime import datetime, timezone

from take_home.causal_chains.agents.agent_runner.protocol.agent_runner import AgentRunner
from take_home.causal_chains.agents.models.messaging.message import MarkdownMessage, Role
from take_home.causal_chains.agents.models.run_clients import RunClients
from take_home.causal_chains.agents.models.run_context import RunContext


class _FixedClock:
    def now(self) -> datetime:
        return datetime(2026, 9, 29, 5, 16, tzinfo=timezone.utc)


class _WithStream:
    async def stream(self, inputs: list[str], context: RunContext):
        if False:
            yield MarkdownMessage(
                message_id="m_1",
                conversation_id="1",
                user_uuid="user-1",
                role=Role.agent,
                text="",
                created_timestamp=datetime(2026, 9, 30, tzinfo=timezone.utc),
            )


class _WithoutStream:
    pass


def test_agent_runner_is_runtime_checkable():
    assert isinstance(_WithStream(), AgentRunner)
    assert not isinstance(_WithoutStream(), AgentRunner)


def test_agent_runner_event_and_context():
    event = MarkdownMessage(
        message_id="m_1",
        conversation_id="1",
        user_uuid="user-1",
        role=Role.agent,
        text="hi",
        created_timestamp=datetime(2026, 9, 30, tzinfo=timezone.utc),
    )
    assert event.kind == "markdown"
    context = RunContext(
        conversation_id="1",
        clock=_FixedClock(),
        turn_id="t_1",
        clients=RunClients(causal_chain_store=object()),
    )
    assert context.turn_id == "t_1"
