import asyncio
import uuid
from collections.abc import AsyncIterator

from take_home.causal_chains.agents.models.messaging.sse_event import (
    SseDelta,
    SseDone,
    SseError,
    SseEvent,
    SseTool,
)
from take_home.causal_chains.agents.models.runner_context import RunnerContext
from take_home.causal_chains.agents.protocol.agent_runner import AgentRunner
from take_home.causal_chains.models.message import Message
from take_home.causal_chains.models.turn import Turn
from take_home.causal_chains.models.turn_status import TurnStatus


class ChatService:
    def __init__(self, agent_runner: AgentRunner) -> None:
        self._agent_runner = agent_runner
        self._turns: dict[str, Turn] = {}
        self._messages: list[Message] = []
        self._buffers: dict[str, list[SseEvent]] = {}
        self._waiters: dict[str, list[asyncio.Queue[SseEvent | None]]] = {}

    def post_message(self, conversation_id: str, text: str) -> Turn:
        turn = Turn(
            turn_id=f"t_{uuid.uuid4().hex[:8]}",
            conversation_id=conversation_id,
            status=TurnStatus.queued,
        )
        self._turns[turn.turn_id] = turn
        self._buffers[turn.turn_id] = []
        self._waiters[turn.turn_id] = []
        self._messages.append(
            Message(
                message_id=f"m_{uuid.uuid4().hex[:8]}",
                conversation_id=conversation_id,
                turn_id=turn.turn_id,
                role="user",
                text=text,
            )
        )
        asyncio.get_running_loop().create_task(self._run_turn(turn, text))
        return turn

    async def subscribe(self, conversation_id: str, turn_id: str) -> AsyncIterator[SseEvent]:
        turn = self._turns.get(turn_id)
        if turn is None or turn.conversation_id != conversation_id:
            yield SseError(message="turn not found")
            return
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

    async def _run_turn(self, turn: Turn, text: str) -> None:
        running = turn.model_copy(update={"status": TurnStatus.running})
        self._turns[turn.turn_id] = running
        try:
            context = RunnerContext(
                conversation_id=turn.conversation_id,
                turn_id=turn.turn_id,
            )
            async for event in self._agent_runner.stream([text], context):
                self._publish(turn.turn_id, event)
                if isinstance(event, SseDone):
                    self._turns[turn.turn_id] = running.model_copy(
                        update={"status": TurnStatus.completed}
                    )
                    return
                if isinstance(event, SseError):
                    self._turns[turn.turn_id] = running.model_copy(
                        update={"status": TurnStatus.failed}
                    )
                    return
            done = SseDone(message_id=f"m_{turn.turn_id}")
            self._publish(turn.turn_id, done)
            self._turns[turn.turn_id] = running.model_copy(
                update={"status": TurnStatus.completed}
            )
        except Exception as error:
            self._publish(turn.turn_id, SseError(message=str(error)))
            self._turns[turn.turn_id] = running.model_copy(
                update={"status": TurnStatus.failed}
            )

    def _publish(self, turn_id: str, event: SseEvent) -> None:
        self._buffers[turn_id].append(event)
        for queue in list(self._waiters.get(turn_id, [])):
            queue.put_nowait(event)


def format_sse(event: SseDelta | SseTool | SseDone | SseError) -> str:
    payload = event.model_dump_json(exclude={"type"})
    return f"event: {event.type}\ndata: {payload}\n\n"
