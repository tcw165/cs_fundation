import uuid
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from typing import Annotated

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
    MarkdownMessage,
    Message,
    Role,
)
from take_home.causal_chains.agents.models.messaging.turn.turn import Turn
from take_home.causal_chains.agents.models.messaging.turn.turn_status import TurnStatus
from take_home.causal_chains.agents.stores.messaging_store.protocol.message_page import (
    MessagePage,
)
from take_home.causal_chains.agents.models.run_config import RunConfig
from take_home.causal_chains.agents.observability.logging import (
    bind_conversation_logger,
    bind_session_logger,
    logger,
)

router = APIRouter()


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

    existing = await turn_store.get_turn_by_conversation(conversation_id)
    if existing is not None:
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
    start_message: Annotated[str | None, Query()] = None,
) -> MessagePage:
    with bind_conversation_logger(conversation_id):
        logger().info("list messages")
        return await container.messaging_store().list_messages(
            conversation_id,
            limit,
            start_message,
        )


def format_conversation_sse(snapshot: ConversationMessagesResponse) -> str:
    return f"event: conversation_messages\ndata: {snapshot.model_dump_json()}\n\n"


@router.get("/conversation/{conversation_id}/turn/{turn_id}/sse")
async def turn_sse(
    conversation_id: str,
    turn_id: str,
    container: AppContainerDep,
    include_traces: Annotated[bool, Query()] = False,
) -> StreamingResponse:
    async def event_stream() -> AsyncIterator[str]:
        with bind_session_logger(conversation_id, turn_id):
            turn = await container.turn_store().get_turn(turn_id)
            stored = (
                await container.messaging_store().list_messages(conversation_id, 100)
            ).messages
            from_message = None if turn is None else turn.from_message
            anchored = next(
                (
                    message
                    for message in stored
                    if getattr(message, "message_id", None) == from_message
                ),
                None,
            )
            if (
                turn is None
                or conversation_id != "1"
                or turn.conversation_id != "1"
                or turn.status is not TurnStatus.queued
                or not isinstance(anchored, MarkdownMessage)
            ):
                return
            chat_service = container.chat_service()
            async for message in chat_service.run_turn(
                turn,
                anchored.text,
                RunConfig(include_traces=include_traces),
            ):
                yield format_conversation_sse(_snapshot(message, turn))

    return StreamingResponse(event_stream(), media_type="text/event-stream")


def _snapshot(message: Message, turn: Turn) -> ConversationMessagesResponse:
    return ConversationMessagesResponse(
        conversation_id="1",
        messages=[message],
        user_interaction_state=UserInteractionState(
            text_input_state=TextInputState.SEND_ENABLED_WITH_STOP_BUTTON,
        ),
        turn=TurnDescriptor(processing=[turn], queued=[]),
    )
