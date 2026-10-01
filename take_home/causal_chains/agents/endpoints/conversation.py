import uuid
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from take_home.causal_chains.agents.chat_service.chat_service import format_sse
from take_home.causal_chains.agents.di.deps import AppContainerDep
from take_home.causal_chains.agents.http_models.post_message_body import PostMessageBody
from take_home.causal_chains.agents.models.messaging.message import (
    MarkdownMessage,
    Role,
)
from take_home.causal_chains.agents.models.messaging.turn import Turn
from take_home.causal_chains.agents.models.messaging.turn_status import TurnStatus
from take_home.causal_chains.agents.models.run_config import RunConfig
from take_home.causal_chains.agents.observability.logging import bind_session_logger

router = APIRouter()


@router.post("/conversation/{conversation_id}/messages", response_model=Turn)
async def post_message(
    conversation_id: str,
    body: PostMessageBody,
    container: AppContainerDep,
) -> Turn:
    message = MarkdownMessage(
        message_id=str(uuid.uuid4()),
        role=Role.user,
        text=body.text,
        created_timestamp=datetime.now(timezone.utc),
    )
    await container.messaging_store().append(conversation_id, message)
    turn = Turn(
        turn_id=f"t_{uuid.uuid4().hex[:8]}",
        conversation_id=conversation_id,
        status=TurnStatus.queued,
        from_message=message.message_id,
    )
    await container.turn_store().put_turn(turn)
    return turn


def _passed_cursor(
    after_message: str,
    from_message: str,
) -> bool:
    return after_message == "" or after_message == from_message


@router.get("/conversation/{conversation_id}/turn/{turn_id}/sse")
async def turn_sse(
    conversation_id: str,
    turn_id: str,
    container: AppContainerDep,
    after_message: Annotated[str, Query()],
    include_traces: Annotated[bool, Query()] = False,
) -> StreamingResponse:
    turn = await container.turn_store().get_turn(turn_id)
    stored = await container.messaging_store().list_messages(conversation_id)
    from_message = None if turn is None else turn.from_message
    anchored = next(
        (
            message
            for message in stored
            if getattr(message, "message_id", None) == from_message
        ),
        None,
    )

    async def event_stream() -> AsyncIterator[str]:
        if (
            turn is None
            or turn.conversation_id != conversation_id
            or turn.status is not TurnStatus.queued
            or not isinstance(anchored, MarkdownMessage)
        ):
            return
        passed = _passed_cursor(after_message, turn.from_message)
        with bind_session_logger(conversation_id, turn_id):
            async for message in container.chat_service().run_turn(
                turn,
                anchored.text,
                RunConfig(include_traces=include_traces),
            ):
                if not passed:
                    if getattr(message, "message_id", None) == after_message:
                        passed = True
                    continue
                yield format_sse(message)

    return StreamingResponse(event_stream(), media_type="text/event-stream")
