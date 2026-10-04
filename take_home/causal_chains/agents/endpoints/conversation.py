import uuid
from collections.abc import AsyncIterator
from functools import partial
from datetime import datetime, timezone
from typing import Annotated

import anyio
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from fastapi.responses import StreamingResponse

from take_home.causal_chains.agents.di.deps import AppContainerDep
from take_home.causal_chains.agents.endpoints.models.conversation_messages_response import (
    ConversationMessagesResponse,
)
from take_home.causal_chains.agents.endpoints.models.peripheral_interaction import (
    CausalChainCase,
    PeripheralInteraction,
)
from take_home.causal_chains.agents.endpoints.models.post_message_response import (
    PostMessageResponse,
)
from take_home.causal_chains.agents.endpoints.models.text_input_state import TextInputState
from take_home.causal_chains.agents.endpoints.models.thinking_state import ThinkingState
from take_home.causal_chains.agents.endpoints.models.turn_descriptor import TurnDescriptor
from take_home.causal_chains.agents.endpoints.models.user_interaction_state import (
    UserInteractionState,
)
from take_home.causal_chains.agents.http_models.post_message_body import PostMessageBody
from take_home.causal_chains.agents.models.messaging.message import (
    MarkdownMessage,
    Message,
    Role,
)
from take_home.causal_chains.agents.models.messaging.protocol.message_base import BaseMessage
from take_home.causal_chains.agents.models.turn.turn import Turn
from take_home.causal_chains.agents.models.turn.turn_status import TurnStatus
from anyio.streams.memory import MemoryObjectSendStream

from take_home.causal_chains.agents.stores.messaging_store.protocol.message_page import (
    MessagePage,
)
from take_home.causal_chains.agents.stores.causal_chain_store.protocol.protocol import (
    CausalChainStore,
)
from take_home.causal_chains.agents.stores.messaging_store.protocol.messaging_store import (
    MessagingStore,
)
from take_home.causal_chains.agents.stores.turn_store.protocol.protocol import TurnStore
from take_home.causal_chains.agents.models.run_config import RunConfig
from take_home.causal_chains.agents.observability.logging import (
    bind_conversation_logger,
    bind_session_logger,
    logger,
)

router = APIRouter(prefix="/api/v1")

_WATCH_TURN_POLL_INTERVAL_S = 0.3
_TAIL_MESSAGES_POLL_INTERVAL_S = 0.5


@router.post(
    "/conversation/{conversation_id}/messages",
    response_model=PostMessageResponse,
)
async def post_message(
    conversation_id: str,
    body: PostMessageBody,
    container: AppContainerDep,
    background_tasks: BackgroundTasks,
) -> PostMessageResponse:
    chat_service = container.chat_service()
    turn_store = container.turn_store()
    messaging_store = container.messaging_store()

    existing_turn = await turn_store.get_turn_by_conversation(conversation_id)
    if existing_turn is not None and not existing_turn.status.is_ended():
        raise HTTPException(status_code=409, detail="conversation already has a turn")

    turn_id = f"t_{uuid.uuid4().hex[:8]}"
    message = MarkdownMessage(
        message_id=str(uuid.uuid4()),
        conversation_id=conversation_id,
        user_uuid="user-1",
        role=Role.user,
        text=body.text,
        created_timestamp=datetime.now(timezone.utc),
    )
    with bind_session_logger(conversation_id, turn_id):
        await messaging_store.append(conversation_id, message)
        turn = Turn(
            turn_id=turn_id,
            conversation_id=conversation_id,
            status=TurnStatus.queued,
            from_message=message.message_id,
        )
        await turn_store.put_turn(turn)
        logger().info("received user message")

        async def _run_turn_in_background() -> None:
            """Keep the agent turn running after the post response returns.

            ``post_message`` stores the user message and the queued turn, then
            returns. This task drives ``chat_service.run_turn`` so those messages
            stay stored and the turn reaches an ended status.
            """
            with bind_session_logger(conversation_id, turn_id):
                async for streamed in chat_service.run_turn(
                    turn=turn,
                    inputs=[message],
                    run_config=RunConfig(),
                ):
                    logger().info(f"streamed message kind={streamed.kind}")

        background_tasks.add_task(_run_turn_in_background)
        logger().info("queued turn")

        return PostMessageResponse(turn=turn, received_message=message)


@router.get("/conversation/{conversation_id}/messages")
async def get_messages(
    conversation_id: str,
    container: AppContainerDep,
    limit: Annotated[int, Query(ge=1, le=100)],
    after_message: Annotated[
        str | None,
        Query(description="Exclusive message id. The page starts after this message. Absent to start at the oldest message."),
    ] = None,
    after_message_timestamp: Annotated[
        datetime | None,
        Query(
            description="created_timestamp of after_message. Required with the message id to find that message. Absent to start at the oldest message.",
        ),
    ] = None,
) -> MessagePage:
    _require_cursor_pair(after_message, after_message_timestamp)
    with bind_conversation_logger(conversation_id):
        logger().info("list messages")
        return await container.messaging_store().list_messages(
            conversation_id=conversation_id,
            limit=limit,
            after_message=after_message,
            after_message_timestamp=after_message_timestamp,
        )


@router.post(
    "/conversation/{conversation_id}/turn/{turn_id}/stop",
    response_model=Turn,
)
async def stop_turn(
    conversation_id: str,
    turn_id: str,
    container: AppContainerDep,
) -> Turn:
    turn_store = container.turn_store()
    turn = await _require(turn_store, conversation_id, turn_id)
    with bind_session_logger(conversation_id, turn_id):
        if turn.status.is_ended():
            return turn
        cancelled = turn.model_copy(update={"status": TurnStatus.cancelled})
        await turn_store.put_turn(cancelled)
        logger().info("stopped turn")
        return cancelled


@router.get("/conversation/{conversation_id}/turn/{turn_id}/sse")
async def turn_sse(
    conversation_id: str,
    turn_id: str,
    container: AppContainerDep,
    after_message: Annotated[
        str | None,
        Query(description="Exclusive message id. The stream starts after this message. Absent to start at the oldest message."),
    ] = None,
    after_message_timestamp: Annotated[
        datetime | None,
        Query(
            description="created_timestamp of after_message. Required with the message id to find that message. Absent to start at the oldest message.",
        ),
    ] = None,
) -> StreamingResponse:
    _require_cursor_pair(after_message, after_message_timestamp)
    turn_store = container.turn_store()
    messaging_store = container.messaging_store()

    opened_turn = await _require(turn_store, conversation_id, turn_id)
    if opened_turn.status.is_ended():
        raise HTTPException(status_code=404, detail="turn already ended")

    async def event_stream() -> AsyncIterator[str]:
        with bind_session_logger(conversation_id, turn_id):
            holder = _PeripheralHolder()
            send, receive = anyio.create_memory_object_stream[Message | None]()
            stop = anyio.Event()

            async with anyio.create_task_group() as group:
                group.start_soon(
                    partial(
                        _watch_turn,
                        turn_store=turn_store,
                        turn_id=turn_id,
                        stop=stop,
                    ),
                )
                group.start_soon(
                    partial(
                        _poll_messages,
                        messaging_store=messaging_store,
                        conversation_id=conversation_id,
                        after_message=after_message,
                        after_message_timestamp=after_message_timestamp,
                        send=send,
                        stop=stop,
                    ),
                )
                group.start_soon(
                    partial(
                        _poll_cases,
                        store=container.causal_chain_store(),
                        conversation_id=conversation_id,
                        holder=holder,
                        send=send,
                        stop=stop,
                    ),
                )

                yield format_conversation_sse(
                    conversation_id=conversation_id,
                    turn=opened_turn,
                    message=None,
                    peripheral_interactions=holder.latest,
                )
                async with receive:
                    async for message in receive:
                        current_turn = await turn_store.get_turn(turn_id)
                        yield format_conversation_sse(
                            conversation_id=conversation_id,
                            turn=current_turn,
                            message=message,
                            peripheral_interactions=holder.latest,
                        )
                end_turn = await turn_store.get_turn(turn_id)
                yield format_conversation_sse(
                    conversation_id=conversation_id,
                    turn=end_turn,
                    message=None,
                    peripheral_interactions=holder.latest,
                )

    return StreamingResponse(event_stream(), media_type="text/event-stream")


def format_conversation_sse(
    conversation_id: str,
    turn: Turn | None,
    message: Message | None,
    peripheral_interactions: list[PeripheralInteraction] | None = None,
) -> str:
    snapshot = _snapshot(
        conversation_id,
        turn,
        message,
        peripheral_interactions,
    )
    return f"event: conversation_messages\ndata: {snapshot.model_dump_json()}\n\n"


class _PeripheralHolder:
    def __init__(self) -> None:
        self.latest: list[PeripheralInteraction] = []


async def _poll_cases(
    store: CausalChainStore,
    conversation_id: str,
    holder: _PeripheralHolder,
    send: MemoryObjectSendStream[Message | None],
    stop: anyio.Event,
) -> None:
    seen: tuple[str, ...] = ()
    try:
        while not stop.is_set():
            cases = await store.list_latest_cases(conversation_id, limit=3)
            latest = [
                CausalChainCase(
                    case_id=str(case.case_id),
                    from_message_id=case.from_message_id,
                )
                for case in cases
            ]
            case_ids = tuple(item.case_id for item in latest)
            holder.latest = latest
            if case_ids != seen:
                seen = case_ids
                await send.send(None)
            await anyio.sleep(_TAIL_MESSAGES_POLL_INTERVAL_S)
    except (anyio.ClosedResourceError, anyio.BrokenResourceError):
        return


async def _watch_turn(
    turn_store: TurnStore,
    turn_id: str,
    stop: anyio.Event,
) -> None:
    try:
        while True:
            current = await turn_store.get_turn(turn_id)
            if current is None or current.status.is_ended():
                return
            await anyio.sleep(_WATCH_TURN_POLL_INTERVAL_S)
    finally:
        stop.set()


async def _poll_messages(
    messaging_store: MessagingStore,
    conversation_id: str,
    after_message: str | None,
    after_message_timestamp: datetime | None,
    send: MemoryObjectSendStream[Message | None],
    stop: anyio.Event,
) -> None:
    try:
        while True:
            page = await messaging_store.list_messages(
                conversation_id=conversation_id,
                limit=100,
                after_message=after_message,
                after_message_timestamp=after_message_timestamp,
            )
            for message in page.messages:
                await send.send(message)
                if isinstance(message, BaseMessage):
                    after_message = message.message_id
                    after_message_timestamp = message.created_timestamp
            if page.next_cursor is not None:
                continue
            if stop.is_set():
                trailing = await messaging_store.list_messages(
                    conversation_id=conversation_id,
                    limit=100,
                    after_message=after_message,
                    after_message_timestamp=after_message_timestamp,
                )
                for message in trailing.messages:
                    await send.send(message)
                return
            await anyio.sleep(_TAIL_MESSAGES_POLL_INTERVAL_S)
    finally:
        await send.aclose()


def _require_cursor_pair(
    after_message: str | None,
    after_message_timestamp: datetime | None,
) -> None:
    if (after_message is None) != (after_message_timestamp is None):
        raise HTTPException(
            status_code=422,
            detail="after_message and after_message_timestamp are a pair",
        )


async def _require(
    turn_store: TurnStore,
    conversation_id: str,
    turn_id: str,
) -> Turn:
    turn = await turn_store.get_turn(turn_id)
    if turn is None or turn.conversation_id != conversation_id:
        raise HTTPException(status_code=404, detail="turn not found")
    return turn


def _snapshot(
    conversation_id: str,
    turn: Turn | None,
    message: Message | None,
    peripheral_interactions: list[PeripheralInteraction] | None = None,
) -> ConversationMessagesResponse:
    in_flight = turn is not None and not turn.status.is_ended()
    return ConversationMessagesResponse(
        conversation_id=conversation_id,
        messages=[] if message is None else [message],
        user_interaction_state=_user_interaction_state(turn),
        turn=TurnDescriptor(
            processing=[turn] if in_flight else [],
            queued=[],
        ),
        peripheral_interactions=(
            [] if peripheral_interactions is None else peripheral_interactions
        ),
    )


def _user_interaction_state(turn: Turn | None) -> UserInteractionState:
    if turn is not None and turn.status == TurnStatus.queued:
        return UserInteractionState(
            text_input_state=TextInputState.SEND_DISABLED,
            thinking_state=ThinkingState(text="Thinking"),
        )
    if turn is not None and turn.status == TurnStatus.running:
        return UserInteractionState(
            text_input_state=TextInputState.SEND_ENABLED_WITH_STOP_BUTTON,
            thinking_state=ThinkingState(text="Thinking"),
        )
    return UserInteractionState(
        text_input_state=TextInputState.ENABLED,
        thinking_state=_thinking_for_ended_turn(turn),
    )


def _thinking_for_ended_turn(turn: Turn | None) -> ThinkingState | None:
    if (
        turn is None
        or turn.status is TurnStatus.completed
        or turn.status is TurnStatus.cancelled
        or turn.status is TurnStatus.timeout
    ):
        return None
    if turn.status is TurnStatus.failed:
        return ThinkingState(text="Failed")
    return None
