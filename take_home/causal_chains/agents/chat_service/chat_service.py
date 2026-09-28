from collections.abc import AsyncIterator

from agents import flush_traces, trace

from take_home.causal_chains.agents.agent_runner.protocol.agent_runner import AgentRunner
from take_home.causal_chains.agents.models.messaging.message import (
    DeeplinkCardMessage,
    HeartbeatMessage,
    MarkdownMessage,
    Message,
)
from take_home.causal_chains.agents.models.messaging.turn import Turn
from take_home.causal_chains.agents.models.messaging.turn_status import TurnStatus
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


class ChatService:
    def __init__(
        self,
        agent_runner: AgentRunner,
        messaging_store: MessagingStore,
        turn_store: TurnStore,
        causal_chain_store: CausalChainStore,
    ) -> None:
        self._agent_runner = agent_runner
        self._messaging_store = messaging_store
        self._turn_store = turn_store
        self._causal_chain_store = causal_chain_store

    async def run_turn(
        self,
        turn: Turn,
        text: str,
        run_config: RunConfig | None = None,
    ) -> AsyncIterator[Message]:
        running = turn.model_copy(update={"status": TurnStatus.running})
        await self._turn_store.put_turn(running)
        context = RunContext(
            conversation_id=turn.conversation_id,
            turn_id=turn.turn_id,
            run_config=run_config or RunConfig(),
            clients=RunClients(
                causal_chain_store=self._causal_chain_store,
            ),
        )
        try:
            with trace(
                workflow_name="chat_service",
                group_id=turn.conversation_id,
                metadata={"turn_id": turn.turn_id},
            ):
                try:
                    async for message in self._agent_runner.stream([text], context):
                        yield message
                    await self._turn_store.put_turn(
                        running.model_copy(update={"status": TurnStatus.completed})
                    )
                except Exception:
                    await self._turn_store.put_turn(
                        running.model_copy(update={"status": TurnStatus.failed})
                    )
                    raise
        finally:
            flush_traces()


def format_sse(
    event: MarkdownMessage | DeeplinkCardMessage | HeartbeatMessage,
) -> str:
    payload = event.model_dump_json(exclude={"type"})
    return f"event: {event.type}\ndata: {payload}\n\n"
