import asyncio
import uuid
from collections.abc import AsyncIterator

from agents import flush_traces, trace

from take_home.causal_chains.agents.agent_runner.protocol.agent_runner import AgentRunner
from take_home.causal_chains.agents.stores.messaging_store.protocol.messaging_store import (
    MessagingStore,
)
from take_home.causal_chains.agents.stores.turn_store.protocol.protocol import TurnStore
from take_home.causal_chains.agents.models.messaging.sse_event import (
    SseDelta,
    SseDone,
    SseError,
    SseEvent,
    SseTool,
)
from take_home.causal_chains.agents.models.run_clients import RunClients
from take_home.causal_chains.agents.models.run_config import RunConfig
from take_home.causal_chains.agents.models.run_context import RunContext
from take_home.causal_chains.agents.stores.causal_chain_store.protocol.protocol import (
    CausalChainStore,
)
from take_home.causal_chains.agents.models.messaging.message import (
    MarkdownMessage,
    Role,
)
from take_home.causal_chains.agents.models.messaging.turn import Turn
from take_home.causal_chains.agents.models.messaging.turn_status import TurnStatus


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
        self._turns: dict[str, Turn] = {}
        self._contexts: dict[str, RunContext] = {}
        self._buffers: dict[str, list[SseEvent]] = {}
        self._waiters: dict[str, list[asyncio.Queue[SseEvent | None]]] = {}

    async def _record_turn(
        self,
        turn: Turn,
    ) -> None:
        self._turns[turn.turn_id] = turn
        await self._turn_store.put_turn(turn)

    async def post_message(
        self,
        conversation_id: str,
        text: str,
    ) -> Turn:
        message_id = str(uuid.uuid4())
        turn = Turn(
            turn_id=f"t_{uuid.uuid4().hex[:8]}",
            conversation_id=conversation_id,
            status=TurnStatus.queued,
            from_message=message_id,
        )
        await self._record_turn(turn)
        self._contexts[turn.turn_id] = RunContext(
            conversation_id=conversation_id,
            turn_id=turn.turn_id,
            clients=RunClients(
                causal_chain_store=self._causal_chain_store,
            ),
        )
        self._buffers[turn.turn_id] = []
        self._waiters[turn.turn_id] = []
        await self._messaging_store.append(
            conversation_id,
            MarkdownMessage(
                message_id=message_id,
                role=Role.user,
                text=text,
            ),
        )
        return turn

    async def subscribe(
        self,
        conversation_id: str,
        turn_id: str,
        run_config: RunConfig | None = None,
    ) -> AsyncIterator[SseEvent]:
        turn = self._turns.get(turn_id)
        if turn is None or turn.conversation_id != conversation_id:
            yield SseError(message="turn not found")
            return
        context = self._contexts.get(turn_id)
        if context is not None and run_config is not None:
            context.run_config = run_config
        queue: asyncio.Queue[SseEvent | None] = asyncio.Queue()
        for event in list(self._buffers[turn_id]):
            yield event
            if event.type in {"done", "error"}:
                return
        self._waiters[turn_id].append(queue)
        try:
            while True:
                event = await queue.get()
                if event is None:
                    return
                yield event
                if event.type in {"done", "error"}:
                    return
        finally:
            waiters = self._waiters.get(turn_id, [])
            if queue in waiters:
                waiters.remove(queue)

    async def run_turn(
        self,
        turn: Turn,
        text: str,
    ) -> None:
        running = turn.model_copy(update={"status": TurnStatus.running})
        await self._record_turn(running)
        try:
            with trace(
                workflow_name="chat_service",
                group_id=turn.conversation_id,
                metadata={"turn_id": turn.turn_id},
            ):
                try:
                    context = self._contexts[turn.turn_id]
                    async for event in self._agent_runner.stream([text], context):
                        self._publish(turn.turn_id, event)
                        if isinstance(event, SseDone):
                            await self._record_turn(
                                running.model_copy(update={"status": TurnStatus.completed})
                            )
                            return
                        if isinstance(event, SseError):
                            await self._record_turn(
                                running.model_copy(update={"status": TurnStatus.failed})
                            )
                            return
                    done = SseDone(message_id=f"m_{turn.turn_id}")
                    self._publish(turn.turn_id, done)
                    await self._record_turn(
                        running.model_copy(update={"status": TurnStatus.completed})
                    )
                except Exception as error:
                    self._publish(turn.turn_id, SseError(message=str(error)))
                    await self._record_turn(
                        running.model_copy(update={"status": TurnStatus.failed})
                    )
        finally:
            flush_traces()

    def _publish(self, turn_id: str, event: SseEvent) -> None:
        self._buffers[turn_id].append(event)
        for queue in list(self._waiters.get(turn_id, [])):
            queue.put_nowait(event)


def format_sse(event: SseEvent) -> str:
    payload = event.model_dump_json(exclude={"type"})
    return f"event: {event.type}\ndata: {payload}\n\n"
