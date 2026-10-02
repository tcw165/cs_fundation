from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from agents import flush_traces, trace

from take_home.causal_chains.agents.agent_runner.protocol.agent_runner import AgentRunner
from take_home.causal_chains.agents.models.messaging.message import (
    HeartbeatMessage,
    MarkdownMessage,
    Message,
    Role,
)
from take_home.causal_chains.agents.models.messaging.message_widgets import (
    DeeplinkCardMessage,
)
from take_home.causal_chains.agents.models.turn.turn import Turn
from take_home.causal_chains.agents.models.turn.turn_status import TurnStatus
from take_home.causal_chains.agents.models.run_clients import RunClients
from take_home.causal_chains.agents.models.run_config import RunConfig
from take_home.causal_chains.agents.models.run_context import RunContext
from take_home.causal_chains.agents.stores.causal_chain_store.protocol.protocol import (
    CausalChainStore,
)
from take_home.causal_chains.agents.stores.messaging_store.protocol.messaging_store import (
    MessagingStore,
)
from take_home.causal_chains.agents.stores.turn_store.protocol.protocol import TurnStore
from take_home.causal_chains.time.protocol.protocol import Clock


def can_store_message(message: Message) -> bool:
    return message.role is Role.user or message.role is Role.agent


@asynccontextmanager
async def update_turn(turn_store: TurnStore, turn: Turn) -> AsyncIterator[None]:
    running = turn.model_copy(update={"status": TurnStatus.running})
    await turn_store.put_turn(running)
    try:
        yield
    except Exception:
        await turn_store.put_turn(
            running.model_copy(update={"status": TurnStatus.failed})
        )
        raise
    else:
        await turn_store.put_turn(
            running.model_copy(update={"status": TurnStatus.completed})
        )


class ChatService:
    def __init__(
        self,
        agent_runner: AgentRunner,
        messaging_store: MessagingStore,
        turn_store: TurnStore,
        causal_chain_store: CausalChainStore,
        clock: Clock,
    ) -> None:
        self._agent_runner = agent_runner
        self._messaging_store = messaging_store
        self._turn_store = turn_store
        self._causal_chain_store = causal_chain_store
        self._clock = clock

    async def run_turn(
        self,
        turn: Turn,
        text: str,
        run_config: RunConfig | None = None,
    ) -> AsyncIterator[Message]:
        try:
            async with update_turn(self._turn_store, turn):
                context = RunContext(
                    conversation_id=turn.conversation_id,
                    clock=self._clock,
                    turn_id=turn.turn_id,
                    run_config=run_config or RunConfig(),
                    clients=RunClients(
                        causal_chain_store=self._causal_chain_store,
                    ),
                )
                with trace(
                    workflow_name="chat_service",
                    group_id=turn.conversation_id,
                    metadata={"turn_id": turn.turn_id},
                ):
                    async for message in self._agent_runner.stream([text], context):
                        if can_store_message(message):
                            await self._messaging_store.append(
                                turn.conversation_id,
                                message,
                            )
                        yield message
        finally:
            flush_traces()


def format_sse(
    event: MarkdownMessage | DeeplinkCardMessage | HeartbeatMessage,
) -> str:
    payload = event.model_dump_json(exclude={"kind"})
    return f"event: {event.kind}\ndata: {payload}\n\n"
