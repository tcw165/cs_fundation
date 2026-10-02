import asyncio
from collections.abc import AsyncGenerator, AsyncIterator
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
from take_home.causal_chains.agents.observability.logging import logger
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
async def update_turn(turn_store: TurnStore, turn: Turn) -> AsyncIterator[bool]:
    if await _turn_is_ended(turn_store, turn.turn_id):
        yield False
        return
    running = turn.model_copy(update={"status": TurnStatus.running})
    await turn_store.put_turn(running)
    try:
        yield True
    except Exception:
        await _put_status_unless_ended(turn_store, running, TurnStatus.failed)
        raise
    else:
        await _put_status_unless_ended(turn_store, running, TurnStatus.completed)


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
            async with update_turn(self._turn_store, turn) as turn_is_open:
                if not turn_is_open:
                    return
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
                    stream = await self._agent_runner.stream([text], context)
                    async for message in stream:
                        if await _turn_is_ended(self._turn_store, turn.turn_id):
                            await _close_stream(stream)
                            break
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


async def _close_stream(stream: AsyncGenerator[Message]) -> None:
    try:
        await stream.aclose()
    except BaseException as error:
        if not _is_cancellation(error):
            raise
        logger().exception("turn stream cancelled")


def _is_cancellation(error: BaseException) -> bool:
    if isinstance(error, asyncio.CancelledError):
        return True
    if isinstance(error, BaseExceptionGroup):
        return all(_is_cancellation(item) for item in error.exceptions)
    return False


async def _turn_is_ended(turn_store: TurnStore, turn_id: str) -> bool:
    current = await turn_store.get_turn(turn_id)
    return current is not None and current.status.is_ended()


async def _put_status_unless_ended(
    turn_store: TurnStore,
    turn: Turn,
    status: TurnStatus,
) -> None:
    if await _turn_is_ended(turn_store, turn.turn_id):
        return
    await turn_store.put_turn(turn.model_copy(update={"status": status}))
