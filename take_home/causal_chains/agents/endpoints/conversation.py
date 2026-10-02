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
from take_home.causal_chains.agents.endpoints.models.post_message_response import (
    PostMessageResponse,
)
from take_home.causal_chains.agents.endpoints.models.text_input_state import TextInputState
from take_home.causal_chains.agents.endpoints.models.turn_descriptor import TurnDescriptor
from take_home.causal_chains.agents.endpoints.models.user_interaction_state import (
    UserInteractionState,
)
from take_home.causal_chains.agents.http_models.post_message_body import PostMessageBody
from take_home.causal_chains.agents.models.messaging.message import (
    HeartbeatMessage,
    MarkdownMessage,
    Message,
    Role,
)
from take_home.causal_chains.agents.models.turn.turn import Turn
from take_home.causal_chains.agents.models.turn.turn_status import TurnStatus
from anyio.streams.memory import MemoryObjectSendStream

from take_home.causal_chains.agents.stores.messaging_store.protocol.message_page import (
    MessagePage,
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

router = APIRouter()

_WATCH_TURN_POLL_INTERVAL_S = 0.3
_TAIL_MESSAGES_POLL_INTERVAL_S = 0.5
_HEARTBEAT_INTERVAL_S = 3.0


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

    async def _run_turn() -> None:
        with bind_session_logger(conversation_id, turn_id):
            async for streamed in chat_service.run_turn(
                turn,
                message.text,
                RunConfig(),
            ):
                logger().info(f"streamed message kind={streamed.kind}")

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

        background_tasks.add_task(_run_turn)
        logger().info("queued turn")
        return PostMessageResponse(turn=turn, received_message=message)


@router.get("/conversation/{conversation_id}/messages")
async def get_messages(
    conversation_id: str,
    container: AppContainerDep,
    limit: Annotated[int, Query(ge=1)],
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
    include_traces: Annotated[bool, Query()] = False,
) -> StreamingResponse:
    _require_cursor_pair(after_message, after_message_timestamp)
    turn_store = container.turn_store()
    messaging_store = container.messaging_store()
    turn = await _require(turn_store, conversation_id, turn_id)
    del include_traces

    async def event_stream() -> AsyncIterator[str]:
        with bind_session_logger(conversation_id, turn_id):
            send, receive = anyio.create_memory_object_stream[Message]()
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
                        _send_heartbeat,
                        send=send,
                        stop=stop,
                    ),
                )
                async with receive:
                    async for message in receive:
                        current_turn = await turn_store.get_turn(turn_id)
                        yield format_conversation_sse(
                            conversation_id=conversation_id,
                            turn=current_turn,
                            message=message,
                        )

    return StreamingResponse(event_stream(), media_type="text/event-stream")


def format_conversation_sse(
    conversation_id: str,
    turn: Turn | None,
    message: Message,
) -> str:
    nullable_turn = turn if turn is not None and not turn.status.is_ended() else None
    snapshot = _snapshot(conversation_id, nullable_turn, message)
    return f"event: conversation_messages\ndata: {snapshot.model_dump_json()}\n\n"


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
    send: MemoryObjectSendStream[Message],
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
            if page.next_cursor is not None:
                after_message = page.next_cursor
                after_message_timestamp = page.messages[-1].created_timestamp
                continue
            if stop.is_set():
                return
            await anyio.sleep(_TAIL_MESSAGES_POLL_INTERVAL_S)
    finally:
        await send.aclose()


async def _send_heartbeat(
    send: MemoryObjectSendStream[Message],
    stop: anyio.Event,
) -> None:
    try:
        while not stop.is_set():
            with anyio.move_on_after(_HEARTBEAT_INTERVAL_S):
                await stop.wait()
            if stop.is_set():
                return
            await send.send(HeartbeatMessage())
    except (anyio.BrokenResourceError, anyio.ClosedResourceError):
        return


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
    message: Message,
) -> ConversationMessagesResponse:
    return ConversationMessagesResponse(
        conversation_id=conversation_id,
        messages=[message],
        user_interaction_state=UserInteractionState(
            text_input_state=TextInputState.SEND_ENABLED_WITH_STOP_BUTTON,
        ),
        turn=TurnDescriptor(
            processing=[] if turn is None else [turn],
            queued=[],
        ),
    )
