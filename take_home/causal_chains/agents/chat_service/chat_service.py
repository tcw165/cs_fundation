import asyncio
import contextlib
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import timedelta
from functools import partial

import anyio
from anyio.streams.memory import MemoryObjectSendStream
from agents import flush_traces, trace

from take_home.causal_chains.agents.agent_runner.protocol.agent_runner import AgentRunner
from take_home.causal_chains.agents.agent_runner.protocol.agent_stream import AgentStream
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

_TURN_POLL_INTERVAL_S = 0.3
_HEARTBEAT_INTERVAL_S = 3.0
_INPUT_WINDOW = timedelta(minutes=10)


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


def format_sse(
    event: MarkdownMessage | DeeplinkCardMessage | HeartbeatMessage,
) -> str:
    payload = event.model_dump_json(exclude={"kind"})
    return f"event: {event.kind}\ndata: {payload}\n\n"


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
        inputs: list[Message],
        run_config: RunConfig,
    ) -> AsyncIterator[Message]:
        """Yield this turn's messages until the agent finishes or the time limit hits.

        ``run_config.agent_timeout_s`` is the limit. The default is 5 minutes.
        ``TimeoutError`` stays inside this method. The generator ends, and
        messages already stored stay stored.

        corner cases:

        when the frontend stops the turn while the agent is still running:
            The stop stores ``cancelled`` and returns before the agent stops.
            The poll calls ``stream.cancel()`` within about 0.3 seconds.
            The time limit does not fire. The stored status stays ``cancelled``.

        when the agent would run past ``agent_timeout_s``:
            The run is cut at the limit, not when the model would have finished.
            Cancelling the turn stops the SDK run without waiting for the model.
            The stored status stays ``running`` through that unwind, then becomes
            ``timeout``.
        """
        send, receive = anyio.create_memory_object_stream[Message]()

        async def _time_bounded_run() -> None:
            """Run the turn until agent_timeout_s, then store status timeout."""
            try:
                await asyncio.wait_for(
                    self._run_turn(
                        turn=turn,
                        inputs=inputs,
                        run_config=run_config,
                        send=send,
                    ),
                    run_config.agent_timeout_s,
                )
            except TimeoutError:
                await _put_turn_status_timeout(self._turn_store, turn)
            finally:
                await send.aclose()

        driver = asyncio.create_task(_time_bounded_run())
        try:
            async with receive:
                async for message in receive:
                    yield message
            await driver
        finally:
            if not driver.done():
                driver.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await driver
            flush_traces()

    def _compute_prewarm_messages(self) -> list[Message]:
        """Messages placed ahead of the conversation when a turn starts.

        created_timestamp starts at 0, then 1, then 2, then 3, and so on.
        A sort from oldest to newest keeps that order ahead of real messages.
        """
        return []

    async def _build_model_messages(
        self,
        conversation_id: str,
        inputs: list[Message],
    ) -> list[Message]:
        """Prewarm messages, the last 10 minutes, and the latest user messages.

        Oldest first. A latest user message already in the window is not repeated.
        """
        prewarm = self._compute_prewarm_messages()
        until = max(message.created_timestamp for message in inputs)
        window = await self._messaging_store.search_messages(
            conversation_id=conversation_id,
            since=until - _INPUT_WINDOW,
            until=until,
        )
        seen = {item.message_id for item in window}
        latest_user_messages = [
            message for message in inputs if message.message_id not in seen
        ]
        return sorted(
            [*prewarm, *window, *latest_user_messages],
            key=lambda message: message.created_timestamp,
        )

    async def _run_turn(
        self,
        turn: Turn,
        inputs: list[Message],
        run_config: RunConfig,
        send: MemoryObjectSendStream[Message],
    ) -> None:
        async with update_turn(self._turn_store, turn) as turn_is_open:
            if not turn_is_open:
                return
            context = RunContext(
                conversation_id=turn.conversation_id,
                clock=self._clock,
                turn_id=turn.turn_id,
                run_config=run_config,
                clients=RunClients(
                    causal_chain_store=self._causal_chain_store,
                    messaging_store=self._messaging_store,
                ),
            )
            with trace(
                workflow_name="chat_service",
                group_id=turn.conversation_id,
                metadata={"turn_id": turn.turn_id},
            ):
                # The coroutine that generates content for the stream starts here.
                model_messages = await self._build_model_messages(
                    conversation_id=turn.conversation_id,
                    inputs=inputs,
                )
                stream = await self._agent_runner.stream(model_messages, context)

                async with anyio.create_task_group() as group:
                    # stream blocks on the model, so the poll has to run beside it.
                    group.start_soon(
                        partial(
                            _cancel_stream_when_turn_ends,
                            turn_store=self._turn_store,
                            turn_id=turn.turn_id,
                            stream=stream,
                        ),
                    )
                    group.start_soon(
                        partial(
                            _send_heartbeat,
                            send=send,
                        ),
                    )

                    async for message in stream:
                        if can_store_message(message):
                            await self._messaging_store.append(
                                turn.conversation_id,
                                message,
                            )
                        await send.send(message)
                    group.cancel_scope.cancel()


async def _send_heartbeat(send: MemoryObjectSendStream[Message]) -> None:
    try:
        while True:
            await anyio.sleep(_HEARTBEAT_INTERVAL_S)
            await send.send(HeartbeatMessage())
    except (anyio.BrokenResourceError, anyio.ClosedResourceError):
        return


async def _cancel_stream_when_turn_ends(
    turn_store: TurnStore,
    turn_id: str,
    stream: AgentStream,
) -> None:
    """Cancel the stream once the stored turn has ended.

    The stream blocks on the model, so this poll runs beside it. Every
    ``_TURN_POLL_INTERVAL_S`` seconds it reads the turn. An ended status
    calls ``stream.cancel()`` and the poll returns.
    """
    while True:
        if await _turn_is_ended(turn_store, turn_id):
            stream.cancel()
            return
        await anyio.sleep(_TURN_POLL_INTERVAL_S)


async def _turn_is_ended(turn_store: TurnStore, turn_id: str) -> bool:
    current = await turn_store.get_turn(turn_id)
    return current is not None and current.status.is_ended()


async def _put_turn_status_timeout(turn_store: TurnStore, turn: Turn) -> None:
    if await _turn_is_ended(turn_store, turn.turn_id):
        return
    await turn_store.put_turn(turn.model_copy(update={"status": TurnStatus.timeout}))


async def _put_status_unless_ended(
    turn_store: TurnStore,
    turn: Turn,
    status: TurnStatus,
) -> None:
    if await _turn_is_ended(turn_store, turn.turn_id):
        return
    await turn_store.put_turn(turn.model_copy(update={"status": status}))
